from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.schemas.auth import UserCreate
from app.crud.user import get_user_by_email, create_user
from fastapi import HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.auth import UserCreate
from app.core.database import get_db

async def register_user(db: AsyncSession, user_data: UserCreate):
    result = await db.execute(select(User).filter(User.email == user_data.email))
    existing_user = result.scalar()

    
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = User(**user_data.model_dump())
    db.add(new_user)
    await db.commit() 
    await db.refresh(new_user) 
    return new_user

