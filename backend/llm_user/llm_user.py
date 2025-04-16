import asyncio
import json
import typing
from typing import Callable, Dict, List, Optional

from mcp import Tool
from pydantic import BaseModel
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
                    k: ParameterProperty(type=v["type"],description=v['title'])
                    for k, v in tool.inputSchema["properties"].items()
                },
                required=list(tool.inputSchema["required"]),
            ),
        ),
    )


sys_mcp = FastMCP()


@sys_mcp.tool()
def summary(content: typing.Annotated[str, "the content to be summarized"]) -> typing.Annotated[str, "the summarized content"]:
    """
    summary the content

    """
    return content


async def main() -> None:
    tools = await sys_mcp.list_tools()
    print(tools)
    print(json.dumps([get_tool_description(tool).model_dump() for tool in tools]))


if __name__ == "__main__":
    asyncio.run(main())
