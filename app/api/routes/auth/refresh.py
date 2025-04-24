from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.validators import RefreshTokenRequest, Token
from app.services.jwt import token_expired, decode_token, create_access_token, create_refresh_token
from app.core.database import get_db
from datetime import timedelta

router = APIRouter()

@router.post("/refresh", response_model=Token)
async def refresh_access_token(refresh_token_request: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    token = refresh_token_request.refresh_token

    if token_expired(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is expired.")

    user = decode_token(token)

    access_token = create_access_token(user["sub"], user["id"], timedelta(days=7))
    refresh_token = create_refresh_token(user["sub"], user["id"], timedelta(days=14))

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
