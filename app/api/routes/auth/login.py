from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.validators import UserLogin, Token
from app.core.database import get_db
from app.services.auth_service import login_user
from app.services.jwt import create_access_token, create_refresh_token, authenticate_user
from datetime import timedelta

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    return await login_user(db, user)

@router.post("/token", response_model=Token, status_code=status.HTTP_200_OK)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: AsyncSession = Depends(get_db)
):
    user = authenticate_user(form_data.username, form_data.password, db)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user.")

    access_token = create_access_token(user.username, user.id, timedelta(days=7))
    refresh_token = create_refresh_token(user.username, user.id, timedelta(days=14))

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
