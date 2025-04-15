from typing import Dict, List
from openai import OpenAI
import os
from backend.database import get_chat_room, get_room_messages
from backend.models import User


class McpUser(User):
    def __init__(self, user: User):
        self.user = user


class LlmUser(User):
    def __init__(self, user: User):
        self.user = user
        self.llm = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com",
        )

    def send_message(self, group_id: str, cur_msg: str):
        pass


class Tool:
    name: str
    args: Dict[str, str]


class Mcp:
    name: str
    description: str
    tools: List[Tool]


all_mcps = {
    "twitter": {
        "name": "twitter",
        "description": "get twitter posts",
        "tools": [
            {
                "name": "get_post_by_username",
                "description": "get twitter posts by username",
                "args": {
                    "username": "str",
                },
            }
        ],
    },
    "calendar_manager": {
        "name": "calendar_manager",
        "description": "manage calendar events",
        "tools": [
            {
                "name": "add_event",
                "description": "add an event to the calendar",
                "args": {
                    "title": "str",
                    "start_time": "str",
                    "end_time": "str",
                    "description": "str",
                },
            },
            {
                "name": "delete_event",
                "description": "delete an event from the calendar",
                "args": {
                    "id": "str",
                },
            },
            {
                "name": "get_events",
                "description": "get all events from the calendar",
                "args": {},
            },
            {
                "name": "get_incoming_events",
                "description": "get all incoming events from the calendar",
                "args": {},
            },
        ],
    },
    "news_search": {
        "name": "news_search",
        "description": "search for news",
        "tools": [
            {
                "name": "search_news",
                "description": "search for news",
                "args": {
                    "keywords": "str",
                    "tags": "str",
                    "country": "str",
                },
            },
            {
                "name": "hot_news",
                "description": "get hot news",
                "args": {},
            },
        ],
    },
}
