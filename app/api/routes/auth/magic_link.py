from fastapi import APIRouter, Depends, HTTPException,Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.core.database import get_db
from app.services.auth.magic_link import send_magic_link
from app.services.auth.jwt import decode_token, create_access_token, create_refresh_token


router = APIRouter()

@router.post("/magic-link")
async def send_link(email: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await send_magic_link(user)
    return {"msg": "Magic link sent"}


@router.post("/magic-login/verify")
async def magic_login_verify(request: Request):
    token = request.query_params.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Token missing")

    user_data = decode_token(token)

    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


    access_token = create_access_token(user_data["sub"], user_data["role"])
    refresh_token = create_refresh_token(user_data["sub"], user_data["role"])

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }
