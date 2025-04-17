from datetime import datetime
import logging

from bson import ObjectId

from backend.db.conn import db
from backend.db.user import get_user_by_id

# 数据库集合
messages_collection = db.messages
chat_rooms_collection = db.chat_rooms



# 消息相关函数
async def save_message(
    content: str, sender_id: str, sender_username: str, room_id: str, mentions: list[dict] = None
):
    message = {
        "content": content,
        "sender_id": sender_id,
        "sender_username": sender_username,
        "room_id": room_id,
        "created_at": datetime.utcnow(),
        "mentions": mentions or []
    }
    result = await messages_collection.insert_one(message)
    message["id"] = str(result.inserted_id)
    return message


async def get_room_messages(room_id: str, limit: int = 50):
    print("room_id:", room_id)

    cursor = messages_collection.find({"room_id": room_id})
    cursor.sort("created_at", -1).limit(limit)
    messages = await cursor.to_list(length=limit)
    return messages


# 聊天室相关函数
async def create_chat_room(name: str, creator_id: str):
    room = {
        "name": name,
        "creator_id": creator_id,
        "participants": [creator_id],
        "created_at": datetime.utcnow(),
        "is_public": True,
    }
    result = await chat_rooms_collection.insert_one(room)
    room["id"] = str(result.inserted_id)
    return room


async def get_chat_room(room_id: str):
    room = await chat_rooms_collection.find_one({"_id": ObjectId(room_id)})
    if room:
        room["id"] = str(room["_id"])
        # Get usernames for participants
    return room


async def add_participant_to_room(room_id: str, user_id: str):
    logging.info(f"add_participant_to_room: {room_id}, {user_id}")
    await chat_rooms_collection.update_one(
        {"_id": ObjectId(room_id)}, {"$addToSet": {"participants": user_id}}
    )



async def get_room_participants(room_id: str):
    room = await get_chat_room(room_id)
    return room["participants"]


async def get_chat_rooms(user_id: str):
    rooms = await chat_rooms_collection.find({"participants": user_id}).to_list(length=100)
    for room in rooms:
        room["id"] = str(room["_id"])
    return rooms

async def get_chat_room_by_id(room_id: str):
    return await chat_rooms_collection.find_one({"_id": ObjectId(room_id)})
