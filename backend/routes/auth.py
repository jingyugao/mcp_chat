from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from backend.db.user import (
    get_user_by_username,
    get_user_by_email,
    create_user,
    verify_password,
    delete_token,
)
from backend.routes.util import get_current_user, create_access_token
from backend.model.model import User, Token


# 创建 Bearer token 验证器
security = HTTPBearer()

router = APIRouter()


class UserLogin(BaseModel):
    username: str
    password: str



@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(user: User):
    # Check if username already exists
    db_user_by_username = await get_user_by_username(user.username)
    if db_user_by_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email already exists
    db_user_by_email = await get_user_by_email(user.email)
    if db_user_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create new user
    await create_user(user)
    return {"message": "User created successfully"}


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    # Get user from database
    user = await get_user_by_username(user_data.username)
    if not user or not verify_password(user_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(days=3)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    # Map the dictionary from DB to the Pydantic model, excluding password
    current_user["password"] = ""
    return current_user


@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    await delete_token(token)
    return {"message": "Successfully logged out"}
