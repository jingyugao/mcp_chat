from calendar import c
from pydoc import cli
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from typing import Optional, Dict, List
from pydantic import BaseModel
from contextlib import AsyncExitStack
from mcp import ClientSession
from mcp.types import ResourceTemplate,Prompt,Resource, Tool
from mcp.client.sse import sse_client
import mcp as mcp

app = FastAPI()

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
    tools: Optional[List[Tool]] = None
    prompts: Optional[List[Prompt]] = None
    resources: Optional[List[Resource]] = None
    resource_templates: Optional[List[ResourceTemplate]] = None

class MCPClient:
    def __init__(self,url: str, name: str):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self._streams_context = None
        self._session_context = None
        self.tools = []
        self.status = "disconnected"
        self.ServerInfo = ServerInfo(url=url, name=name)

    async def connect_to_sse_server(self, server_url: str):
        """Connect to an MCP server running with SSE transport"""
        try:
            # Store the context managers so they stay alive
            self._streams_context = sse_client(url=server_url)
            streams = await self._streams_context.__aenter__()

            self._session_context = ClientSession(*streams)
            self.session: ClientSession = await self._session_context.__aenter__()

            # Initialize
            await self.session.initialize()

            # List available tools to verify connection
            response = await self.session.list_tools()
            self.ServerInfo.tools = response.tools
            response = await self.session.list_prompts()
            self.ServerInfo.prompts =  response.prompts
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
        try:
            if self._session_context:
                await self._session_context.__aexit__(None, None, None)
            if self._streams_context:
                await self._streams_context.__aexit__(None, None, None)
            self.status = "disconnected"
            self.session = None
            self.ServerInfo.tools = []
            self.ServerInfo.prompts = []
            self.ServerInfo.resources = []
            self.ServerInfo.resource_templates = []

        except Exception as e:
            print(f"Error during cleanup: {str(e)}")


mcp_clients: Dict[str, MCPClient] = {}


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
            resource_templates=client.ServerInfo.resource_templates
        )
        for _, client in mcp_clients.items()
    ]




@app.post("/api/add_server")
async def add_server(server_info: ServerInfo):
    """Add a new server to the registry"""
    if server_info.name in mcp_clients:
        return {"status": "error", "message": "Server already exists"}
    mcp_clients[server_info.name] = MCPClient(server_info.url,server_info.name)
    return {"status": "success", "message": "Server added successfully"}



@app.post("/api/connect_server")
async def connect_server(name: str):
    """Connect to a registered server"""
    if name not in mcp_clients:
        raise HTTPException(status_code=404, detail=f"Server {name} not found")
    
        
    client = mcp_clients[name]   
    if client.status == "connected":
        client.cleanup()
        
    
    success = await client.connect_to_sse_server(client.ServerInfo.url)
    if success:
        return {
            "status": "success", 
            "message": "Server connected successfully",
        }
    else:
        raise HTTPException(
            status_code=500, 
            detail="Failed to connect to server"
        )

@app.delete("/api/remove_server")
async def remove_server(name: str):
    """Remove a server from the registry"""
    if name not in mcp_clients:
        raise HTTPException(status_code=404, detail="Server not found")
    
    client = mcp_clients[name]
    await client.cleanup()
    del mcp_clients[name]
    return {"status": "success", "message": "Server removed successfully"}

class ToolExecuteRequest(BaseModel):
    server: str
    tool: str
    parameters: dict

@app.post("/api/execute_tool")
async def execute_tool(request: ToolExecuteRequest):
    """Execute a tool on a server"""
    if request.server not in mcp_clients:
        raise HTTPException(status_code=404, detail="Server not found")
    
    client = mcp_clients[request.server]
    if client.status != "connected":
        raise HTTPException(status_code=400, detail="Server not connected")
    
    try:
        result = await client.session.execute_tool(request.tool, request.parameters)
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        timeout_graceful_shutdown=10
    )
    server = uvicorn.Server(config)
    

    server.run()
