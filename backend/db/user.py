from datetime import datetime

from bson import ObjectId
from passlib.context import CryptContext

from backend.db.conn import users_collection, tokens_collection
from backend.model.model import User

# 密码哈希
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def get_user_by_username(username: str):
    return await users_collection.find_one({"username": username})


async def get_user_by_email(email: str):
    return await users_collection.find_one({"email": email})


async def create_user(user: User):
    user_dict = {
        "username": user.username,
        "email": user.email,
        "password": pwd_context.hash(user.password),
        "created_at": datetime.utcnow(),
        "role": user.role,
    }
    result = await users_collection.insert_one(user_dict)
    user_dict["id"] = str(result.inserted_id)
    return user_dict


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


async def delete_user_tokens(username: str):
    await tokens_collection.delete_many({"username": username})


async def get_token(token: str):
    return await tokens_collection.find_one({"token": token})


async def save_token(username: str, token: str, expires: datetime):
    await tokens_collection.insert_one(
        {"username": username, "token": token, "expires": expires}
    )


async def delete_token(token: str):
    await tokens_collection.delete_one({"token": token})


async def get_user_by_id(user_id: str):
    return await users_collection.find_one({"_id": ObjectId(user_id)})


async def search_user(username: str, user_id: str):
    return await users_collection.find(
        {"username": f"/{username}/", "_id": {"$ne": user_id}}
    ).to_list(length=100)

async def get_users_by_ids(user_ids: list[str]):
    return await users_collection.find({"_id": {"$in": [ObjectId(user_id) for user_id in user_ids]}}).to_list(length=100)
