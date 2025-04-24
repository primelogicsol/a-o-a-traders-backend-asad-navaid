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


ALGORITHM = "HS256"
SECRET_KEY = os.getenv("SECRET_KEY")
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
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(username: str, user_id: int, role: str, expires_delta: timedelta):
    return create_access_token(username, user_id, role, expires_delta)


def decode_token(token: str):
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


async def get_current_user(
    db: AsyncSession,
    token: Annotated[str, Depends(oauth_bearer)]
):
    try:
        payload = decode_token(token)
        username = payload.get("sub")
        user_id = payload.get("id")
        role = payload.get("role")

        if not username or not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate user."
            )

        stmt = select(User).options(
            defer(User.password), defer(User.google_sub)
        ).where(User.username == username)

        result = await db.execute(stmt)
        user = result.scalars().first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )

        return {"username": username, "user_id": user_id, "role": role, "user": user}

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token."
        )

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
