from datetime import timedelta, datetime, timezone
from typing import Annotated
from fastapi import Depends, HTTPException
from jose import jwt, JWTError
from starlette import status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import defer
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
import os
from app.schemas.auth.auth import UserResponse
from app.core.database import get_db

ALGORITHM = "HS256"
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")


async def authenticate_user(db: AsyncSession, username: str, password: str):
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    user: User = result.scalars().first()

    if not user or not bcrypt_context.verify(password, user.password):
        return False
    return user

def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta):
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {
        "sub": username,
        "id": user_id,
        "role": role,
        "exp": expire
    }
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)



def create_refresh_token(username: str, user_id: int, role: str, expires_delta: timedelta):
    return create_access_token(username, user_id, role, expires_delta)


def decode_token(token: str):
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])


async def get_current_user(token: Annotated[str, Depends(oauth_bearer)], db: AsyncSession = Depends(get_db)) -> UserResponse:
    try:
        payload = decode_token(token)
        user_id = payload.get("id")
        role = payload.get("role")  

        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        

        return UserResponse.model_validate(user)

    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid token")

    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid token")


def token_expired(token: Annotated[str, Depends(oauth_bearer)]):
    try:
        payload = decode_token(token)
        exp = datetime.fromtimestamp(payload.get("exp"), timezone.utc)
        return exp <= datetime.now(timezone.utc)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate token."
        )
