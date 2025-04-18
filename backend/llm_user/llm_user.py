import asyncio
import json
import logging
import threading
import typing
from typing import Callable, Dict, List, Optional

from mcp import Tool
from pydantic import BaseModel
from backend.chat_room import room_chat
from backend.db.chat_room import add_participant_to_room, get_chat_room, get_room_participants
from backend.db.user import create_user, get_user_by_username
from backend.model.model import User, UserRole
from backend.models import Message as BaseMessage

from mcp.server.fastmcp import FastMCP


class ToolCall(BaseModel):
    name: str
    args: dict
    result: dict
    func: Callable


class Message(BaseMessage):
    pass


"""

1.
chat_with_tools(特朗普最近都做了什么。)
content = tools(twitter,news)
chat_summary(content)

2. 
chat_with_tools(关注近期的黄金波动)
subscribe(investment_market(黄金)) in 3 days
chat_summary(content)

3. 
chat_with_tools(今天A股市场如何)
content = tools(investment_market,news)
chat_summary(content)


// 
sys_tools:
subscribe
summary
reminder

ext_tools:


"""


def get_recommend_mcp(history: list[Message], msg: Message):
    pass


def chat_with_tools(history: list[Message], msg: Message):
    pass


all_mcp = {
    "twitter": {
        "name": "twitter",
        "description": "twitter is a social media platform",
        "tools": {
            "get_user_latest_posts": {
                "description": "get the user's latest posts",
                "args": {"user_id": str},
            }
        },
    },
}


class ParameterProperty(BaseModel):
    type: str
    description: Optional[str] = None


class Parameters(BaseModel):
    type: str = "object"
    properties: Dict[str, ParameterProperty]
    required: List[str] = []


class FunctionSchema(BaseModel):
    name: str
    description: str
    parameters: Parameters


class ToolDescription(BaseModel):
    type: str = "function"
    function: FunctionSchema


class McpTool(BaseModel):
    desc: ToolDescription
    func: Callable


def call_tool(tool: Tool, args: dict):
    pass


# client = get_connected_client(request.server)

# result = await client.session.call_tool(tool.name, args)
# return {"status": "success", "result": result}


def get_tool_description(tool: Tool):
    return ToolDescription(
        type="function",
        function=FunctionSchema(
            name=tool.name,
            description=tool.description,
            parameters=Parameters(
                type="object",
                properties={
                    k: ParameterProperty(type=v["type"], description=v["title"])
                    for k, v in tool.inputSchema["properties"].items()
                },
                required=list(tool.inputSchema["required"]),
            ),
        ),
    )

class LlmUser:
    def __init__(self, user_name: str):
        self.user_name = user_name
        self.user = None 
        self.inited=False
        self.user_id =""

    async def start(self):
        user = await get_user_by_username(self.user_name)
        if user is None:
            user = await create_user(
                User(
                    username=self.user_name,
                    password=self.user_name,
                    email=self.user_name+"@llm.com",
                    role=UserRole.LLM,
                )
            )

        if user is None:
            raise Exception("Failed to create llm user")
        self.user = user
        self.user_id = str(user["_id"])
        self.inited=True
        asyncio.create_task(self.task_chat())
        asyncio.create_task(self.task_enter_room())

    async def task_chat(self) -> None:
        while True:
            message = await room_chat.chat_room_manager.global_message_queue.get()
            content = message["data"]["content"]
            sender_id = message["data"]["sender_id"]
            room_id = message["data"]["room_id"]
            mentions = [m['user_id'] for m in  message["data"]["mentions"]]
            if self.user_id in mentions:
                # 回复消息
                await room_chat.chat_room_manager.send_message("你好。我是llm",self.user_id,self.user_name,room_id)
            
            # room_chat.chat_room_manager.send_message("你好。我是llm",self.user_id,self.user_name,message["room_id"],mentions=message['sender_id'])
        
    async def task_enter_room(self) -> None:
        while True:
            message = await room_chat.chat_room_manager.enter_room_queue.get()
            _, room_id = message
            room_participants = await get_room_participants(room_id)
            if self.user_id not in room_participants:
                await add_participant_to_room(room_id=room_id,user_id=self.user_id)


all_llm_users = [LlmUser(user_name="llm_user")]

sys_mcp = FastMCP()


@sys_mcp.tool()
def summary(
    content: typing.Annotated[str, "the content to be summarized"],
) -> typing.Annotated[str, "the summarized content"]:
    """
    summary the content

    """
    return content


def init_task():
    for llm_user in all_llm_users:
        asyncio.create_task(llm_user.start())






def init_llm_user():
    init_task()
