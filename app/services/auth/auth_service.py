from fastapi import HTTPException,status
from fastapi import HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.auth.auth import UserCreate,UserRole
from app.schemas.auth.validators import UserLogin,Token
from app.core.security import get_password_hash,verify_password
from app.services.auth.jwt import create_access_token,create_refresh_token
from datetime import timedelta

async def authenticate_user(db: AsyncSession, email: str, password: str):
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    if not verify_password(password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    return user


async def login_user(db: AsyncSession, user_login: UserLogin) -> Token:

    user = await authenticate_user(db, user_login.email, user_login.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    expires_delta_access = timedelta(hours=1) 
    expires_delta_refresh = timedelta(days=7)  

    access_token = create_access_token(
        username=user.username,
        user_id=user.id,
        role=user.role.value,
        expires_delta=expires_delta_access
    )
    
    refresh_token = create_refresh_token(
        username=user.username,
        user_id=user.id,
        role=user.role.value,
        expires_delta=expires_delta_refresh
    )
    
    return Token(access_token=access_token, token_type="bearer", refresh_token=refresh_token, user_role=user.role.value,
        user_id=user.id )


async def register_user(db: AsyncSession, user_data: UserCreate):
 try:
    result = await db.execute(
        select(User).where((User.email == user_data.email) | (User.username == user_data.username))
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        if existing_user.email == user_data.email:
            raise HTTPException( detail="Email already registered")
        if existing_user.username == user_data.username:
            raise HTTPException( detail="Username already taken")
    
    hashed_pw = get_password_hash(user_data.password)

    new_user = User(
        email=user_data.email,
        username=user_data.username,
        role=UserRole.buyer,
        password=hashed_pw 
    )
    db.add(new_user)
    await db.commit() 
    await db.refresh(new_user) 
    return new_user

 except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
 

async def register_supplier(db: AsyncSession, user_data: UserCreate):
 try:
    result = await db.execute(
        select(User).where((User.email == user_data.email) | (User.username == user_data.username))
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        if existing_user.email == user_data.email:
            raise HTTPException(status_code=400, detail="Email already registered")
        if existing_user.username == user_data.username:
            raise HTTPException(status_code=400, detail="Username already taken")
    
    hashed_pw = get_password_hash(user_data.password)

    new_user = User(
        email=user_data.email,
        username=user_data.username,
        role=UserRole.supplier,
        password=hashed_pw 
    )
    db.add(new_user)
    await db.commit() 
    await db.refresh(new_user) 
    return new_user

 except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


async def register_admin(db: AsyncSession, user_data: UserCreate):
 try:
    result = await db.execute(
        select(User).where((User.email == user_data.email) | (User.username == user_data.username))
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        if existing_user.email == user_data.email:
            raise HTTPException(status_code=400, detail="Email already registered")
        if existing_user.username == user_data.username:
            raise HTTPException(status_code=400, detail="Username already taken")
    
    hashed_pw = get_password_hash(user_data.password)

    new_user = User(
        email=user_data.email,
        username=user_data.username,
        role=UserRole.admin,
        password=hashed_pw 
    )
    db.add(new_user)
    await db.commit() 
    await db.refresh(new_user) 
    return new_user

 except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")