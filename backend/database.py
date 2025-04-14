import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .models import User, UserCreate, TokenData
import asyncio

# MongoDB连接
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGODB_URL)
db = client.chat_db

# 密码哈希
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 数据库集合
users_collection = db.users
messages_collection = db.messages
chat_rooms_collection = db.chat_rooms
tokens_collection = db.tokens  # New collection for tokens

# 创建 Bearer token 验证器
security = HTTPBearer()


async def get_user_by_username(username: str):
    return await users_collection.find_one({"username": username})


async def get_user_by_email(email: str):
    return await users_collection.find_one({"email": email})


async def create_user(username: str, email: str, hashed_password: str):
    user = {
        "username": username,
        "email": email,
        "hashed_password": hashed_password,
        "created_at": datetime.utcnow(),
        "last_login": None,
    }
    result = await users_collection.insert_one(user)
    user["id"] = str(result.inserted_id)
    return user


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


async def save_token(token: str, user_id: str):
    expires_at = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    await tokens_collection.insert_one(
        {"token": token, "user_id": user_id, "expires_at": expires_at}
    )


async def get_current_user(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except jwt.JWTError:
        return None

    token_doc = await tokens_collection.find_one(
        {"token": token, "expires_at": {"$gt": datetime.utcnow()}}
    )
    if not token_doc:
        return None

    user = await users_collection.find_one({"_id": user_id})
    if user:
        await update_user_last_login(user_id)
    return user


async def update_user_last_login(user_id: str):
    await users_collection.update_one(
        {"_id": user_id}, {"$set": {"last_login": datetime.utcnow()}}
    )


async def cleanup_expired_tokens():
    await tokens_collection.delete_many({"expires_at": {"$lt": datetime.utcnow()}})


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    # Store token in MongoDB
    asyncio.create_task(save_token(encoded_jwt, data["sub"]))
    return encoded_jwt


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    try:
        token = credentials.credentials
        # Check if token exists in MongoDB
        token_data = await get_current_user(token)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is invalid or expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token_data = TokenData(username=username)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await get_user_by_username(username=token_data.username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# 消息相关函数
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


async def get_room_messages(room_id: str, limit: int = 50):
    cursor = messages_collection.find({"room_id": room_id})
    cursor.sort("created_at", -1).limit(limit)
    messages = await cursor.to_list(length=limit)
    return messages


# 聊天室相关函数
async def create_chat_room(name: str, creator_id: str):
    room = {"name": name, "created_at": datetime.utcnow(), "participants": [creator_id]}
    result = await chat_rooms_collection.insert_one(room)
    room["id"] = str(result.inserted_id)
    return room


async def get_chat_room(room_id: str):
    return await chat_rooms_collection.find_one({"_id": room_id})


async def add_participant_to_room(room_id: str, user_id: str):
    await chat_rooms_collection.update_one(
        {"_id": room_id}, {"$addToSet": {"participants": user_id}}
    )
