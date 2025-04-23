from typing import Dict, List, Optional
from mcp import ClientSession
from mcp.types import ResourceTemplate, Prompt, Resource, Tool
from pydantic import BaseModel
from backend.chat_room import room_chat
from backend.db.chat_room import get_chat_room
from backend.db.user import get_user_by_username, get_users_by_ids, get_users_by_role
from backend.db.user import create_user
from backend.model.model import User
from backend.model.model import UserRole
from mcp.client.sse import sse_client


class ServerInfo(BaseModel):
    name: str
    url: str
    status: str = None
    tools: Optional[List[Tool]] = []
    prompts: Optional[List[Prompt]] = []
    resources: Optional[List[Resource]] = []
    resource_templates: Optional[List[ResourceTemplate]] = []


class McpUser:
    def __init__(self, user: Dict):
        self.user = user
        self.user_id = str(user["_id"])
        self.user_name = user["username"]
        self.sse_url = user["mcp_sse_url"]
        self.tools = []
        self.prompts = []
        self.resources = []
        self.resource_templates = []

    async def chat_can_exec(self, room_id: str, tool_name: str, args: dict) -> None:
        content = "can exec tool:" + tool_name + " with args:" + str(args)
        room_chat.chat_room_manager.send_message(
            content, self.user_id, self.user_name, room_id
        )

    async def chat_exec_tool(self, room_id: str, msg_id: str) -> None:
        content = "exec tool:" + msg_id
        room_chat.chat_room_manager.send_message(
            content, self.user_id, self.user_name, room_id
        )
    async def send_ping(self):
        async with sse_client(self.sse_url) as client:
            async with ClientSession(*client) as session:
                await session.initialize()
                await session.send_ping()
    
    async def execute_tool(self, tool_name: str, args: dict) -> None:
        async with sse_client(self.sse_url) as client:
            async with ClientSession(*client) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, args)
                return result
        
    async def list_tools(self) -> List[Tool]:
        async with sse_client(self.sse_url) as client:
            async with ClientSession(*client) as session:
                await session.initialize()
                tools = await session.list_tools()
                return tools.tools

    async def refresh_server_info(self) -> ServerInfo:
        async with sse_client(self.sse_url) as client:
            async with ClientSession(*client) as session:
                await session.initialize()
                self.tools=await session.list_tools().tools
                self.prompts=await session.list_prompts().prompts
                self.resources=await session.list_resources().resources
                self.resource_templates=await session.list_resource_templates().resourceTemplates


    async def get_server_info(self) -> ServerInfo:
        async with sse_client(self.sse_url) as client:
            async with ClientSession(*client) as session:
                await session.initialize()
                tools=await session.list_tools()
                prompts=await session.list_prompts()
                resources=await session.list_resources()
                resource_templates=await session.list_resource_templates()

                return ServerInfo(
                    name=self.user_name,
                    url=self.sse_url,
                    status="connected",
                    tools=tools.tools,
                    prompts=prompts.prompts,
                    resources=resources.resources,
                    resource_templates=resource_templates.resourceTemplates
                )


async def create_mcp_user(user_name:str,sse_url:str):
    user = await get_user_by_username(user_name)
    if user is not None:
        raise Exception("User already exists")

    user = await create_user(
        User(
            username=user_name,
            password=user_name,
            email=user_name + "@mcp.com",
            role=UserRole.MCP,
            mcp_sse_url=sse_url
        )
    )
 
    
    return McpUser(user)


async def get_mcp_user(user_name:str):
    user = await get_user_by_username(user_name)
    if user is None:
        return None
    if user["role"] != UserRole.MCP:
        return None
    return McpUser(user)


async def all_mcp_users():
    users = await get_users_by_role(UserRole.MCP)
    return [McpUser(user) for user in users]


async def get_room_mcp_users(room_id: str) -> List[McpUser]:
    room = await get_chat_room(room_id)
    users = await get_users_by_ids(room["participants"])
    return [McpUser(user) for user in users if user["role"]  == UserRole.MCP]
