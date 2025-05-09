import logging
from typing import Dict, Set

import asyncio
from backend.db.chat_room import save_message


# SSE connection manager
from typing import Dict


class ChatRoomManager:
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, asyncio.Queue]] = {}
        self.global_message_queue = asyncio.Queue()
        self.enter_room_queue = asyncio.Queue() 
    async def enter_room(self, user_id: str, room_id: str):
        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}
        if user_id not in self.active_connections[room_id]:
            self.active_connections[room_id][user_id] = asyncio.Queue()
        await self.enter_room_queue.put((user_id,room_id))
        return self.active_connections[room_id][user_id]


    def disconnect(self, user_id: str, room_id: str):
        if room_id in self.active_connections:
            if user_id in self.active_connections[room_id]:
                del self.active_connections[room_id][user_id]
                if not self.active_connections[room_id]:
                    del self.active_connections[room_id]

    async def broadcast(self, message: dict, room_id: str):
        if room_id in self.active_connections:
            for user_id in self.active_connections[room_id]:
                await self.active_connections[room_id][user_id].put(message)
        await self.global_message_queue.put(message)

    async def send_message(
        self, content: str, user_id: str, user_name: str, room_id: str, mentions: list = None
    ):
        logging.info(f"send_message: {content} {user_id} {user_name} {room_id} {mentions}")
        saved_message = await save_message(
            content=content,
            sender_id=user_id,
            sender_username=user_name,
            room_id=room_id,
            mentions=mentions
        )
        await self.broadcast(
            {
                "type": "message",
                "data": {
                    "id": str(saved_message["_id"]),
                    "content": saved_message["content"],
                    "sender_id": saved_message["sender_id"],
                    "sender_username": saved_message["sender_username"],
                    "created_at": saved_message["created_at"].isoformat(),
                    "mentions": saved_message.get("mentions", []),
                    "room_id": room_id,
                },
            },
            room_id,
        )
        return saved_message


chat_room_manager = ChatRoomManager()
