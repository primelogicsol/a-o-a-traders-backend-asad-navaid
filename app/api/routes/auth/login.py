from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.auth.validators import UserLogin, Token
from app.core.database import get_db
from app.services.auth.auth_service import login_user
from app.services.auth.jwt import create_access_token, create_refresh_token, authenticate_user
from datetime import timedelta

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    return await login_user(db, user)

