import bson
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)
from backend.chat_room.room_chat import chat_room_manager as room_chat
from backend.db.user import get_users_by_ids, search_user, get_user_by_username
from backend.routes.util import get_current_user
from backend.db.chat_room import (
    get_room_messages,
    create_chat_room,
    get_chat_room,
    add_participant_to_room,
    get_chat_rooms,
)


from typing import List
import json
from datetime import datetime
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
import os
from sse_starlette.sse import EventSourceResponse
from backend.model.model import ChatRoom, Message


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


# Routes
router = APIRouter()


@router.get("/room_list", response_model=List[ChatRoom])
async def get_rooms(current_user: dict = Depends(get_current_user)):
    ret = await get_chat_rooms(str(current_user["_id"]))
    return ret


@router.post("/create_room", response_model=ChatRoom)
async def create_room(params: dict, current_user: dict = Depends(get_current_user)):
    return await create_chat_room(params["name"], str(current_user["_id"]))


@router.get("/room_info/{room_id}", response_model=ChatRoom)
async def get_room_info(room_id: str, current_user: dict = Depends(get_current_user)):
    room = await get_chat_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    users = await get_users_by_ids(room["participants"])
    room["participant_users"] = {str(user["_id"]): user["username"] for user in users}
    return room


@router.get("/room_messages/{room_id}", response_model=List[Message])
async def get_messages(room_id: str, current_user: dict = Depends(get_current_user)):

    messages = await get_room_messages(room_id)

    return messages


@router.post("/room_messages/{room_id}")
async def send_message(
    room_id: str, message: dict, current_user: dict = Depends(get_current_user)
):
    await room_chat.send_message(
        message["content"], 
        str(current_user["_id"]), 
        current_user["username"], 
        room_id,
        message.get("mentions", [])
    )
    return {"status": "success"}


@router.get("/room_events/{room_id}")
async def sse_endpoint(
    request: Request, room_id: str, current_user: dict = Depends(get_current_user)
):
    async def event_generator():
        queue = await room_chat.enter_room(current_user["_id"], room_id)
        try:
            while True:
                if await request.is_disconnected():
                    break
                message = await queue.get()
                yield {"event": "message", "data": json.dumps(message)}
        finally:
            room_chat.disconnect(current_user["_id"], room_id)

    return EventSourceResponse(event_generator())


@router.get("/user/search")
async def search_user(username: str, current_user: dict = Depends(get_current_user)):
    return await search_user(username, str(current_user["_id"]))


@router.post("/invite_user/{room_id}")
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

    return {
        "status": "success",
        "message": f"User {user_to_invite['username']} has been invited to the room",
    }
