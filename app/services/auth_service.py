from fastapi import HTTPException,status
from fastapi import HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.auth import UserCreate
from app.schemas.validators import UserLogin,Token
from app.core.security import get_password_hash,verify_password
from app.services.jwt import create_access_token,create_refresh_token

async def authenticate_user(db: AsyncSession, email: str, password: str):
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    if not verify_password(password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    return user


async def login_user(db: AsyncSession, user_login: UserLogin) -> Token:
    user = await authenticate_user(db, user_login.email, user_login.password)  # Pass db first
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value
    }
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)  
    
    return Token(access_token=access_token, token_type="bearer", refresh_token=refresh_token)


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

