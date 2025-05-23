from sqlalchemy import Column, Integer, String, Enum, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class UserRole(str, enum.Enum):
    admin = "admin"
    supplier = "supplier"
    buyer = "buyer"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.buyer)
    is_active = Column(Boolean, default=True)
    

    products = relationship("Product", back_populates="supplier") 
    upload_logs = relationship("UploadLog", back_populates="supplier")
    certifications = relationship("Certification", back_populates="supplier")

   