from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.auth.auth import UserCreate, UserResponse
from app.core.database import get_db
from app.services.auth.auth_service import register_user,register_admin,register_supplier

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await register_user(db, user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/register-admin", response_model=UserResponse)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await register_admin(db, user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/register-supplier", response_model=UserResponse)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await register_supplier(db, user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
