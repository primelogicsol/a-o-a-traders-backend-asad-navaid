from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.core.database import get_db
from app.services.magic_link import send_magic_link

router = APIRouter()

@router.post("/magic-link")
async def send_link(email: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await send_magic_link(user)
    return {"msg": "Magic link sent"}
