from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.auth import UserCreate, UserResponse
from app.core.database import get_db
from app.services.auth_service import register_user

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await register_user(db, user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
