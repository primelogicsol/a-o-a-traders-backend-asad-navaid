from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.auth.validators import UserLogin, Token
from app.core.database import get_db
from app.services.auth.auth_service import login_user


router = APIRouter()

@router.post("/login", response_model=Token)
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    return await login_user(db, user)

