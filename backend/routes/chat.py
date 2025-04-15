import bson
from fastapi import (
    APIRouter,
    Depends,
    status,
    HTTPException,
    Request,
)
from typing import Annotated, Dict, Optional, Set, List
import json
from datetime import datetime
from pydantic import BaseModel, BeforeValidator, Field
from motor.motor_asyncio import AsyncIOMotorClient
import os
import asyncio
from sse_starlette.sse import EventSourceResponse
from backend.models import ChatRoom, User, Message, ChatRoom
from backend.database import (
    save_message,
    get_room_messages,
    create_chat_room,
    get_chat_room,
    add_participant_to_room,
    get_current_user,
    get_user_by_username,
    get_chat_rooms,
)


class InviteRequest(BaseModel):
    username: str


# Database setup
MONGODB_URL = os.getenv("MONGODB_URI")
client = AsyncIOMotorClient(MONGODB_URL)
db = client.chat_db
messages_collection = db.messages
chat_rooms_collection = db.chat_rooms


# Database functions
async def save_message(
    content: str, sender_id: str, sender_username: str, room_id: str
):
    message = {
        "content": content,
        "sender_id": sender_id,
        "sender_username": sender_username,
        "room_id": room_id,
        "created_at": datetime.utcnow(),
    }
    result = await messages_collection.insert_one(message)
    message["id"] = str(result.inserted_id)
    return message


async def get_chat_room(room_id: str):
    ret = await chat_rooms_collection.find_one({"_id": bson.ObjectId(room_id)})

    return ret


# SSE connection manager
class SSEManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[asyncio.Queue]] = {}

    async def connect(self, room_id: str):
        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()
        queue = asyncio.Queue()
        self.active_connections[room_id].add(queue)
        return queue

    def disconnect(self, queue: asyncio.Queue, room_id: str):
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(queue)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast(self, message: dict, room_id: str):
        if room_id in self.active_connections:
            for queue in self.active_connections[room_id]:
                await queue.put(message)


manager = SSEManager()

# Routes
router = APIRouter()


@router.get("/chat-rooms/list", response_model=List[ChatRoom])
async def get_rooms(current_user: dict = Depends(get_current_user)):
    ret = await get_chat_rooms(str(current_user["_id"]))
    return ret


@router.post("/chat-rooms", response_model=ChatRoom)
async def create_room(params: dict, current_user: dict = Depends(get_current_user)):
    return await create_chat_room(params["name"], str(current_user["_id"]))


@router.get("/chat-rooms/room-info/{room_id}", response_model=ChatRoom)
async def get_room_info(room_id: str, current_user: dict = Depends(get_current_user)):
    room = await get_chat_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@router.get("/chat-rooms/{room_id}/messages", response_model=List[Message])
async def get_messages(room_id: str, current_user: dict = Depends(get_current_user)):

    messages = await get_room_messages(room_id)

    return messages


@router.post("/chat-rooms/{room_id}/messages")
async def send_message(
    room_id: str, message: dict, current_user: dict = Depends(get_current_user)
):
    saved_message = await save_message(
        content=message["content"],
        sender_id=str(current_user["_id"]),
        sender_username=current_user["username"],
        room_id=room_id,
    )

    await manager.broadcast(
        {
            "type": "message",
            "data": {
                "id": str(saved_message["_id"]),
                "content": saved_message["content"],
                "sender_id": saved_message["sender_id"],
                "sender_username": saved_message["sender_username"],
                "created_at": saved_message["created_at"].isoformat(),
            },
        },
        room_id,
    )
    return {"status": "success"}


@router.get("/chat-rooms/{room_id}/events")
async def sse_endpoint(
    request: Request, room_id: str, current_user: dict = Depends(get_current_user)
):
    async def event_generator():
        queue = await manager.connect(room_id)
        try:
            while True:
                if await request.is_disconnected():
                    break
                message = await queue.get()
                yield {"event": "message", "data": json.dumps(message)}
        finally:
            manager.disconnect(queue, room_id)
            await manager.broadcast(
                {
                    "type": "system",
                    "data": f"User {current_user['username']} left the chat",
                },
                room_id,
            )

    return EventSourceResponse(event_generator())


@router.get("/user/search")
async def search_user(username: str, current_user: dict = Depends(get_current_user)):
    return await search_user(username, str(current_user["_id"]))


@router.post("/chat-rooms/{room_id}/invite")
async def invite_user(
    room_id: str,
    invite_request: InviteRequest,
    current_user: dict = Depends(get_current_user),
):
    # Get the room
    room = await get_chat_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Check if the current user is a participant
    if str(current_user["_id"]) not in room["participants"]:
        raise HTTPException(
            status_code=403, detail="You are not a participant of this room"
        )

    # Get the user to invite
    user_to_invite = await get_user_by_username(invite_request.username)
    if not user_to_invite:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if user is already in the room
    if str(user_to_invite["_id"]) in room["participants"]:
        raise HTTPException(status_code=400, detail="User is already in the room")

    # Add user to room
    await add_participant_to_room(room_id, str(user_to_invite["_id"]))

    # Create system message
    system_message = await save_message(
        content=f"User {user_to_invite['username']} has been invited to the room by {current_user['username']}",
        sender_id="system",
        sender_username="system",
        room_id=room_id,
    )

    # Broadcast the system message
    await manager.broadcast(
        {
            "type": "system",
            "data": {
                "id": str(system_message["_id"]),
                "content": system_message["content"],
                "sender_id": "system",
                "sender_username": "system",
                "created_at": system_message["created_at"].isoformat(),
            },
        },
        room_id,
    )

    return {
        "status": "success",
        "message": f"User {user_to_invite['username']} has been invited to the room",
    }
