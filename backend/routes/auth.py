from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials
from ..database import (
    get_user_by_username,
    get_user_by_email,
    create_user,
    verify_password,
    create_access_token,
    get_current_user,
    delete_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    security
)
from ..models import UserCreate, Token, User, UserLogin

router = APIRouter()

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    # Check if username already exists
    db_user_by_username = await get_user_by_username(user.username)
    if db_user_by_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    db_user_by_email = await get_user_by_email(user.email)
    if db_user_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
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
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    # Map the dictionary from DB to the Pydantic model, excluding password
    user_data = {k: v for k, v in current_user.items() if k != 'password'}
    # Ensure the id is correctly mapped if it's stored as _id
    if '_id' in user_data:
        user_data['id'] = str(user_data['_id'])
    
    # Return the User model
    return User(**user_data)

@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    await delete_token(token)
    return {"message": "Successfully logged out"} 