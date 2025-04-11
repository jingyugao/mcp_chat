import asyncio
from calendar import c
import os
from pydoc import cli
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import traceback

from typing import Optional, Dict, List
from pydantic import BaseModel

from mcp import ClientSession
from mcp.types import ResourceTemplate, Prompt, Resource, Tool
from mcp.client.sse import sse_client
import mcp as mcp

from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.ERROR, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI()


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
        self.tools = []
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

            print(f"Connected to server with tools: {self.tools}")
            return True
        except Exception as e:
            print(f"Failed to connect to server: {str(e)}")
            await self.cleanup()
            self.status = "error"
            return False

    async def cleanup(self):
        """Properly clean up the session and streams"""

        self.status = "disconnected"
        self.session = None
        self._session_context = None
        self._streams_context = None
        self.ServerInfo.tools = []
        self.ServerInfo.prompts = []
        self.ServerInfo.resources = []
        self.ServerInfo.resource_templates = []


mcp_clients: Dict[str, MCPClient] = {
    "default": MCPClient(url="http://127.0.0.1:9999/sse", name="default")
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
    client = get_connected_client(name)
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


@app.post("/api/process_query")
async def process_query(query: str) -> str:
    """Process a query using Claude and available tools"""
    client = get_connected_client("default")
    messages = [{"role": "user", "content": query}]

    response = await client.session.list_tools()
    available_tools = [
        {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema,
        }
        for tool in response.tools
    ]
    return ""


from openai import OpenAI


client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)


def get_tools():
    tools = []
    for client in mcp_clients.values():
        for tool in client.ServerInfo.tools:
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema,
                    },
                },
            )
    return tools


def send_messages(messages):
    print("all_tools", get_tools())
    response = client.chat.completions.create(
        model="deepseek-chat", messages=messages, tools=get_tools()
    )
    return response.choices[0].message


async def devToolCall():
    client = mcp_clients["default"]
    await client.connect_to_sse_server()
    messages = [{"role": "user", "content": "Translate Hello to Chinese."}]
    message = send_messages(messages)
    print("tool_calls", message.tool_calls)
    tool = message.tool_calls[0]
    messages.append(message)

    messages.append({"role": "tool", "tool_call_id": tool.id, "content": "宁好"})
    message = send_messages(messages)
    print(f"Model>\t {message.content}")


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

    asyncio.run(devToolCall())

    server.run()
