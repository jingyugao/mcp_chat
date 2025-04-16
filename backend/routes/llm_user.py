from typing import Callable, Dict, List, Optional
from pydantic import BaseModel
from backend.models import Message as BaseMessage

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

class ToolCall(BaseModel):
    name: str
    args: dict
    result: dict
    func: Callable

def get_tool_metadata(tool: ToolDescription) -> dict:
    return {
        "type": "function",
        "function": {
            "name": tool.function.name,
            "description": tool.function.description,
            "parameters": tool.function.parameters.dict(),
        },
    }

def chat_with_tools(history: list[BaseMessage], msg: BaseMessage):
    pass

def get_recommend_mcp(history: list[BaseMessage], msg: BaseMessage):
    pass 