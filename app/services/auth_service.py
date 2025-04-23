from fastapi import HTTPException
from sqlalchemy.orm import Session
from fastapi import HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.auth import UserCreate
import bcrypt
from app.core.security import get_password_hash

# async def get_user_by_email(db:AsyncSession,email:str):
#     return db.query(User).filter(User.email==email).first()

async def register_user(db: AsyncSession, user_data: UserCreate):
 try:
    result = await db.execute(select(User).filter(User.email == user_data.email))
    existing_user = result.scalar()

    
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pw = get_password_hash(user_data.password)

    new_user = User(
        email=user_data.email,
        username=user_data.username,
        role=user_data.role,
        password=hashed_pw 
    )
    db.add(new_user)
    await db.commit() 
    await db.refresh(new_user) 
    return new_user

 except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

