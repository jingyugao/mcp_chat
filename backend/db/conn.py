import os

from motor.motor_asyncio import AsyncIOMotorClient


# MongoDB连接
MONGODB_URI = os.getenv("MONGODB_URI")
client = AsyncIOMotorClient(MONGODB_URI)
db = client.chat_db



# 数据库集合
users_collection = db.users
tokens_collection = db.tokens

# 数据库集合
messages_collection = db.messages
chat_rooms_collection = db.chat_rooms

