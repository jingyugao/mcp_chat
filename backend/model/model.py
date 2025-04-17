from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

from backend.model.base import MongoBaseModel


class Message(MongoBaseModel):
    content: str
    sender_id: str
    sender_username: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChatRoom(MongoBaseModel):
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    participants: list[str] = Field(default_factory=list)
    participant_names: list[str] = Field(default_factory=list)
    is_public: bool = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    SYSTEM = "system"
    LLM = "llm"
    MCP = "mcp"


class User(MongoBaseModel):
    username: str
    email: str
    password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    role: UserRole = Field(default=UserRole.USER)
