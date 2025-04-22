from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.auth import UserCreate, UserResponse
from app.services.auth_service import register_user
from app.core.database import get_db

router=APIRouter(prefix="/auth",tags=["Auth"])


@router.post("/register",response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        return await register_user(db, user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))