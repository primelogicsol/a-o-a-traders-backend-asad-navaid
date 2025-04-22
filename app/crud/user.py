from sqlalchemy.orm import Session
from fastapi import Depends
from app.models.user import User
from app.schemas.auth import UserCreate
from app.core.database import get_db

def get_user_by_email(db:Session,email:str):
    return db.query(User).filter(User.email==email).first()

def create_user(user:UserCreate,db:Session = Depends(get_db)):
    db_user=User(
        email=user.email,
        username=user.username,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user