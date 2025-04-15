import os
from bson import ObjectId
import bson
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from fastapi.security.utils import get_authorization_scheme_param
from .models import User, UserCreate, TokenData
import asyncio

# MongoDB连接
MONGODB_URI = os.getenv("MONGODB_URI")
client = AsyncIOMotorClient(MONGODB_URI)
db = client.chat_db

# JWT配置
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"



# 密码哈希
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 数据库集合
users_collection = db.users
messages_collection = db.messages
chat_rooms_collection = db.chat_rooms
tokens_collection = db.tokens  # New collection for tokens

# 创建 Bearer token 验证器
security = HTTPBearer()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

async def get_user_by_username(username: str):
    return await users_collection.find_one({"username": username})

async def get_user_by_email(email: str):
    return await users_collection.find_one({"email": email})

async def create_user(user: UserCreate):
    hashed_password = pwd_context.hash(user.password)
    user_dict = {
        "username": user.username,
        "email": user.email,
        "password": hashed_password,
        "created_at": datetime.utcnow()
    }
    result = await users_collection.insert_one(user_dict)
    user_dict["id"] = str(result.inserted_id)
    return user_dict

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

async def save_token(username: str, token: str, expires: datetime):
    await tokens_collection.insert_one({
        "username": username,
        "token": token,
        "expires": expires
    })

async def get_token(token: str):
    return await tokens_collection.find_one({
        "token": token,
        "expires": {"$gt": datetime.utcnow()}
    })

async def delete_token(token: str):
    await tokens_collection.delete_one({"token": token})

async def delete_user_tokens(username: str):
    await tokens_collection.delete_many({"username": username})

# Cleanup expired tokens periodically
async def cleanup_expired_tokens():
    await tokens_collection.delete_many({
        "expires": {"$lt": datetime.utcnow()}
    })

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=3)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    # Store token in MongoDB
    asyncio.create_task(save_token(data["sub"], encoded_jwt, expire))
    return encoded_jwt

async def get_token_from_request(request: Request) -> Optional[str]:
    # First try to get token from query parameters
    token = request.query_params.get("token")
    if token:
        return token
    
    # Then try to get token from header
    authorization = request.headers.get("Authorization")
    if not authorization:
        return None
        
    scheme, token = get_authorization_scheme_param(authorization)
    if scheme.lower() != "bearer":
        return None
        
    return token

async def get_current_user(request: Request):
    token = await get_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Check if token exists in MongoDB
        token_data = await get_token(token)
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
    except (jwt.JWTError, HTTPException):
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
async def save_message(content: str, sender_id: str, sender_username: str, room_id: str):
    message = {
        "content": content,
        "sender_id": sender_id,
        "sender_username": sender_username,
        "room_id": room_id,
        "created_at": datetime.utcnow()
    }
    result = await messages_collection.insert_one(message)
    message["id"] = str(result.inserted_id)
    return message

async def get_room_messages(room_id: str, limit: int = 50):
    print("room_id:",room_id)
    
    
    cursor = messages_collection.find({"room_id": room_id})
    cursor.sort("created_at", -1).limit(limit)
    messages = await cursor.to_list(length=limit)
    return messages

# 聊天室相关函数
async def create_chat_room(name: str, creator_id: str):
    room = {
        "name": name,
        "created_at": datetime.utcnow(),
        "participants": [creator_id]
    }
    result = await chat_rooms_collection.insert_one(room)
    room["id"] = str(result.inserted_id)
    return room

async def get_chat_room(room_id: str):
    return await chat_rooms_collection.find_one({"_id": ObjectId(room_id)})

async def add_participant_to_room(room_id: str, user_id: str):
    await chat_rooms_collection.update_one(
        {"_id": room_id},
        {"$addToSet": {"participants": user_id}}
    ) 
    
    
async def get_chat_rooms(user_id: str):
    return await chat_rooms_collection.find({"participants": user_id}).to_list(length=100)

async def get_chat_room_by_id(room_id: str):
    return await chat_rooms_collection.find_one({"_id": ObjectId(room_id)})

async def search_user(username: str, user_id: str):
    return await users_collection.find({"username": f'/{username}/', "_id": {"$ne": user_id}}).to_list(length=100)
