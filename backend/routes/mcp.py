import asyncio
from fastapi import (
    APIRouter,
    HTTPException,
)

from typing import Optional, Dict, List
from pydantic import BaseModel

from mcp import ClientSession
from mcp.types import ResourceTemplate, Prompt, Resource, Tool
from mcp.client.sse import sse_client
from backend.llm_user.mcp_user import (
    McpUser,
    all_mcp_users,
    create_mcp_user,
    get_mcp_user,
)


router = APIRouter()


class ServerInfo(BaseModel):
    name: str
    url: str
    status: str = None
    tools: Optional[List[Tool]] = []
    prompts: Optional[List[Prompt]] = []
    resources: Optional[List[Resource]] = []
    resource_templates: Optional[List[ResourceTemplate]] = []


# class MCPClient:
#     def __init__(self, url: str, name: str):
#         # Initialize session and client objects
#         self.session: Optional[ClientSession] = None
#         self._streams_context = None
#         self._session_context = None
#         self.status = "disconnected"
#         self.ServerInfo = ServerInfo(url=url, name=name)

#     async def connect_to_sse_server(self):
#         """Connect to an MCP server running with SSE transport"""
#         try:
#             # Store the context managers so they stay alive
#             self._streams_context = sse_client(url=self.ServerInfo.url)
#             streams = await self._streams_context.__aenter__()

#             self._session_context = ClientSession(*streams)
#             self.session: ClientSession = await self._session_context.__aenter__()

#             # Initialize
#             await self.session.initialize()

#             # List available tools to verify connection
#             response = await self.session.list_tools()
#             self.ServerInfo.tools = response.tools
#             response = await self.session.list_prompts()
#             self.ServerInfo.prompts = response.prompts
#             response = await self.session.list_resources()
#             self.ServerInfo.resources = response.resources

#             response = await self.session.list_resource_templates()
#             self.ServerInfo.resource_templates = response.resourceTemplates

#             self.status = "connected"

#             return True
#         except Exception as e:
#             print(f"Failed to connect to server: {str(e)}")
#             await self.cleanup()
#             self.status = "error"
#             return False

#     async def cleanup(self):
#         """Properly clean up the session and streams"""
#         try:
#             if self._session_context:
#                 await self._session_context.__aexit__(None, None, None)
#             if self._streams_context:
#                 await self._streams_context.__aexit__(None, None, None)
#         except Exception as e:
#             pass
#         finally:
#             self.status = "disconnected"
#             self.session = None
#             self._session_context = None
#             self._streams_context = None
#             self.ServerInfo.tools = []
#             self.ServerInfo.prompts = []
#             self.ServerInfo.resources = []
#             self.ServerInfo.resource_templates = []


# mcp_clients: Dict[str, MCPClient] = {
#     "default": MCPClient(url="http://host.docker.internal:9999/sse", name="default")
# }


def get_connected_client(name: str) -> McpUser:
    return get_mcp_user(name)


@router.get("/servers")
async def list_servers() -> List[ServerInfo]:
    """List all registered servers and their status"""
    
    tasks = [client.get_server_info() for client in await all_mcp_users()]
    return await asyncio.gather(*tasks)


@router.post("/add_server")
async def add_server(server_info: ServerInfo):
    """Add a new server to the registry"""
    if await get_mcp_user(server_info.name) is not None:
        raise HTTPException(status_code=400, detail="Server already exists")
    await create_mcp_user(server_info.name, server_info.url)
    return {"status": "success", "message": "Server added successfully"}


@router.post("/connect_server")
async def connect_server(name: str):
    """Connect to a registered server"""
    mu = get_mcp_user(name)
    if mu is None:
        raise HTTPException(status_code=404, detail="Server not found")
    pass;
    return {
        "status": "success",
        "message": "Server connected successfully",
    }


@router.post("/disconnect_server")
async def disconnect_server(name: str):
    """Disconnect a server from the registry"""
    pass;
    return {"status": "success", "message": "Server disconnected successfully"}


@router.delete("/remove_server")
async def remove_server(name: str):
    """Remove a server from the registry"""
    pass;
    
    return {"status": "success", "message": "Server removed successfully"}


class ToolExecuteRequest(BaseModel):
    server: str
    tool: str
    parameters: dict


@router.post("/execute_tool")
async def execute_tool(request: ToolExecuteRequest):
    """Execute a tool on a server"""
    client = get_mcp_user(request.server)

    try:
        result = await client.execute_tool(request.tool, request.parameters)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class GetPromptRequest(BaseModel):
    server: str
    prompt: str
    parameters: dict


@router.post("/get_prompt")
async def get_prompt(request: GetPromptRequest):
    """Get a prompt from a server"""
    client = get_mcp_user(request.server)

    try:
        result = await client.get_prompt(request.prompt, request.parameters)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ResourceFetchRequest(BaseModel):
    server: str
    resource: str


@router.post("/fetch_resource")
async def fetch_resource(request: ResourceFetchRequest):
    """Fetch a resource from a server"""
    client = get_mcp_user(request.server)

    try:
        result = await client.session.read_resource(request.resource)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/list_tool_of_chat")
async def list_tool_of_chat(request: Dict[str, str]):
    pass
    # """List tools of chat"""
    # messages = [{"role": "user", "content": request["content"]}]
    # response = llm.chat.completions.create(
    #     model="deepseek-chat", messages=messages, tools=get_tools()
    # )
    # message = response.choices[0].message
    # print(message)
    # return {
    #     "status": "success",
    #     "result": message.tool_calls,
    # }
