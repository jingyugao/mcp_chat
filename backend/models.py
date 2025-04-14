from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class UserBase(BaseModel):
    username: str
    email: str


class UserCreate(UserBase):
    password: str


class User(BaseModel):
    id: str = Field(default_factory=str)
    username: str
    email: str
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None


class UserLogin(BaseModel):
    username: str
    password: str


class Message(BaseModel):
    id: str = Field(default_factory=str)
    content: str
    sender_id: str
    sender_username: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChatRoom(BaseModel):
    id: str = Field(default_factory=str)
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    participants: list[str] = Field(default_factory=list)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
