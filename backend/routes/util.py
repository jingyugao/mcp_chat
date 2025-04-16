import asyncio
from datetime import datetime, timedelta
from typing import Optional
import os
import jwt
from fastapi import HTTPException, status, Request
from fastapi.security import HTTPBearer, OAuth2PasswordBearer
from backend.db.user import get_user_by_username, get_token,save_token
# JWT配置
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=3)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    asyncio.create_task(save_token(data["sub"], encoded_jwt, expire))
    return encoded_jwt


# 从请求中获取token
async def get_token_from_request(request: Request) -> Optional[str]:
    # First try to get token from query parameters
    token = request.query_params.get("token")
    if token:
        return token

    # Then try to get token from header
    authorization = request.headers.get("Authorization")
    if not authorization:
        return None
    scheme, token = authorization.split()
    if scheme.lower() != "bearer":
        return None
    return token

# 获取当前用户
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
    except (jwt.PyJWTError, HTTPException) as e:
        print("error",e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await get_user_by_username(username=username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
