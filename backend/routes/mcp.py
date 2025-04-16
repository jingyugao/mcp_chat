from fastapi import (
    APIRouter,
    HTTPException,
)

from typing import Optional, Dict, List
from pydantic import BaseModel

from mcp import ClientSession
from mcp.types import ResourceTemplate, Prompt, Resource, Tool
from mcp.client.sse import sse_client


router = APIRouter()


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
            pass
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


@router.get("/servers")
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


@router.post("/add_server")
async def add_server(server_info: ServerInfo):
    """Add a new server to the registry"""
    if server_info.name in mcp_clients:
        return {"status": "error", "message": "Server already exists"}
    mcp_clients[server_info.name] = MCPClient(server_info.url, server_info.name)
    return {"status": "success", "message": "Server added successfully"}


@router.post("/connect_server")
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


@router.post("/disconnect_server")
async def disconnect_server(name: str):
    """Disconnect a server from the registry"""
    client = mcp_clients[name]
    await client.cleanup()
    return {"status": "success", "message": "Server disconnected successfully"}


@router.delete("/remove_server")
async def remove_server(name: str):
    """Remove a server from the registry"""
    await disconnect_server(name)
    del mcp_clients[name]
    return {"status": "success", "message": "Server removed successfully"}


class ToolExecuteRequest(BaseModel):
    server: str
    tool: str
    parameters: dict


@router.post("/execute_tool")
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


@router.post("/get_prompt")
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


@router.post("/fetch_resource")
async def fetch_resource(request: ResourceFetchRequest):
    """Fetch a resource from a server"""
    client = get_connected_client(request.server)

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

