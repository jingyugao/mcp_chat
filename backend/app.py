import asyncio
from calendar import c
from contextlib import asynccontextmanager
import os
from pydoc import cli
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import traceback
import json

from typing import Optional, Dict, List, Set
from pydantic import BaseModel

from mcp import ClientSession
from mcp.types import ResourceTemplate, Prompt, Resource, Tool
from mcp.client.sse import sse_client
import mcp as mcp
from openai import OpenAI

from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta

from .models import UserCreate, User, Message, ChatRoom, Token
from .database import (
    create_user, get_user_by_username, get_user_by_email,
    verify_password, create_access_token, get_current_user,
    save_message, get_room_messages, create_chat_room,
    get_chat_room, add_participant_to_room,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.ERROR, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI()


llm = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)


# Error handling middleware
@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        # Log the full error with traceback
        logger.error(f"Error occurred: {str(e)}\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error occurred"}
        )


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ServerInfo(BaseModel):
    name: str
    url: str
    status: str = None
    tools: Optional[List[Tool]] = []
    prompts: Optional[List[Prompt]] = []
    resources: Optional[List[Resource]] = []
    resource_templates: Optional[List[ResourceTemplate]] = []


class MCPClient:
    def __init__(self, url: str, name: str):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self._streams_context = None
        self._session_context = None
        self.status = "disconnected"
        self.ServerInfo = ServerInfo(url=url, name=name)

    async def connect_to_sse_server(self):
        """Connect to an MCP server running with SSE transport"""
        try:
            # Store the context managers so they stay alive
            self._streams_context = sse_client(url=self.ServerInfo.url)
            streams = await self._streams_context.__aenter__()

            self._session_context = ClientSession(*streams)
            self.session: ClientSession = await self._session_context.__aenter__()

            # Initialize
            await self.session.initialize()

            # List available tools to verify connection
            response = await self.session.list_tools()
            self.ServerInfo.tools = response.tools
            response = await self.session.list_prompts()
            self.ServerInfo.prompts = response.prompts
            response = await self.session.list_resources()
            self.ServerInfo.resources = response.resources

            response = await self.session.list_resource_templates()
            self.ServerInfo.resource_templates = response.resourceTemplates

            self.status = "connected"

            return True
        except Exception as e:
            print(f"Failed to connect to server: {str(e)}")
            await self.cleanup()
            self.status = "error"
            return False

    async def cleanup(self):
        """Properly clean up the session and streams"""
        try:
            if self._session_context:
                await self._session_context.__aexit__(None, None, None)
            if self._streams_context:
                await self._streams_context.__aexit__(None, None, None)
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
        finally:
            self.status = "disconnected"
            self.session = None
            self._session_context = None
            self._streams_context = None
            self.ServerInfo.tools = []
            self.ServerInfo.prompts = []
            self.ServerInfo.resources = []
            self.ServerInfo.resource_templates = []


mcp_clients: Dict[str, MCPClient] = {
    "default": MCPClient(url="http://host.docker.internal:9999/sse", name="default")
}


def get_connected_client(name: str) -> MCPClient:
    if name not in mcp_clients:
        raise HTTPException(status_code=404, detail="Server not found")
    if mcp_clients[name].status != "connected":
        raise HTTPException(status_code=400, detail="Server not connected")
    return mcp_clients[name]


@app.get("/api/servers")
async def list_servers() -> List[ServerInfo]:
    """List all registered servers and their status"""
    return [
        ServerInfo(
            url=client.ServerInfo.url,
            status=client.status,
            name=client.ServerInfo.name,
            tools=client.ServerInfo.tools,
            prompts=client.ServerInfo.prompts,
            resources=client.ServerInfo.resources,
            resource_templates=client.ServerInfo.resource_templates,
        )
        for _, client in mcp_clients.items()
    ]


@app.post("/api/add_server")
async def add_server(server_info: ServerInfo):
    """Add a new server to the registry"""
    if server_info.name in mcp_clients:
        return {"status": "error", "message": "Server already exists"}
    mcp_clients[server_info.name] = MCPClient(server_info.url, server_info.name)
    return {"status": "success", "message": "Server added successfully"}


@app.post("/api/connect_server")
async def connect_server(name: str):
    """Connect to a registered server"""
    if name not in mcp_clients:
        raise HTTPException(status_code=404, detail="Server not found")
    client = mcp_clients[name]
    if client.status == "connected":
        await client.cleanup()
    success = await client.connect_to_sse_server()
    if success:
        return {
            "status": "success",
            "message": "Server connected successfully",
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to connect to server")


@app.post("/api/disconnect_server")
async def disconnect_server(name: str):
    """Disconnect a server from the registry"""
    client = mcp_clients[name]
    await client.cleanup()
    return {"status": "success", "message": "Server disconnected successfully"}


@app.delete("/api/remove_server")
async def remove_server(name: str):
    """Remove a server from the registry"""
    await disconnect_server(name)
    del mcp_clients[name]
    return {"status": "success", "message": "Server removed successfully"}


class ToolExecuteRequest(BaseModel):
    server: str
    tool: str
    parameters: dict


@app.post("/api/execute_tool")
async def execute_tool(request: ToolExecuteRequest):
    """Execute a tool on a server"""
    client = get_connected_client(request.server)

    try:
        result = await client.session.call_tool(request.tool, request.parameters)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class GetPromptRequest(BaseModel):
    server: str
    prompt: str
    parameters: dict


@app.post("/api/get_prompt")
async def get_prompt(request: GetPromptRequest):
    """Get a prompt from a server"""
    client = get_connected_client(request.server)

    try:
        result = await client.session.get_prompt(request.prompt, request.parameters)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ResourceFetchRequest(BaseModel):
    server: str
    resource: str


@app.post("/api/fetch_resource")
async def fetch_resource(request: ResourceFetchRequest):
    """Fetch a resource from a server"""
    client = get_connected_client(request.server)

    try:
        result = await client.session.read_resource(request.resource)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/subscribe_resource")
async def subscribe_resource(request: ResourceFetchRequest):
    """Fetch a resource from a server"""
    client = get_connected_client(request.server)

    try:
        result = await client.session.subscribe_resource(request.resource)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_tools():
    tools = []
    for client in mcp_clients.values():
        for tool in client.ServerInfo.tools:
            tools.append(get_tool_metadata(tool))
    return tools


def get_tool_metadata(tool: Tool):
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.inputSchema,
        },
    }


@app.post("/api/dev/list_tool_of_chat")
async def list_tool_of_chat(request: Dict[str, str]):
    """List tools of chat"""
    messages = [{"role": "user", "content": request["content"]}]
    response = llm.chat.completions.create(
        model="deepseek-chat", messages=messages, tools=get_tools()
    )
    message = response.choices[0].message
    print(message)
    return {
        "status": "success",
        "result": message.tool_calls,
    }


# OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# WebSocket连接管理
class ConnectionManager:
    def __init__(self):
        # room_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()
        self.active_connections[room_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, room_id: str):
        self.active_connections[room_id].remove(websocket)
        if not self.active_connections[room_id]:
            del self.active_connections[room_id]
    
    async def broadcast(self, message: dict, room_id: str):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                await connection.send_json(message)

manager = ConnectionManager()

# 认证相关接口
@app.post("/register", response_model=User)
async def register(user: UserCreate):
    db_user = await get_user_by_username(user.username)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    db_user = await get_user_by_email(user.email)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    return await create_user(user)

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await get_user_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# 聊天室相关接口
@app.post("/chat-rooms", response_model=ChatRoom)
async def create_room(
    name: str,
    current_user: User = Depends(get_current_user)
):
    return await create_chat_room(name, str(current_user["_id"]))

@app.get("/chat-rooms/{room_id}/messages")
async def get_messages(
    room_id: str,
    current_user: User = Depends(get_current_user)
):
    messages = await get_room_messages(room_id)
    return messages

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    token: str
):
    user = await get_current_user(token)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    await manager.connect(websocket, room_id)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # 保存消息到数据库
            message = await save_message(
                content=message_data["content"],
                sender_id=str(user["_id"]),
                sender_username=user["username"],
                room_id=room_id
            )
            
            # 广播消息给房间内所有用户
            await manager.broadcast({
                "type": "message",
                "data": {
                    "id": str(message["_id"]),
                    "content": message["content"],
                    "sender_id": message["sender_id"],
                    "sender_username": message["sender_username"],
                    "created_at": message["created_at"].isoformat()
                }
            }, room_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        await manager.broadcast({
            "type": "system",
            "data": f"User {user['username']} left the chat"
        }, room_id)
    except Exception as e:
        manager.disconnect(websocket, room_id)
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)


if __name__ == "__main__":

    import uvicorn

    # Configure uvicorn server with proper cleanup
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=14000,
        loop="asyncio",
        reload=True,
        timeout_keep_alive=30,
        timeout_graceful_shutdown=10,
    )

    server = uvicorn.Server(config)
    server.run()
