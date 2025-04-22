from pydantic import BaseModel,EmailStr
from enum import Enum

class UserRole(str,Enum):
    admin = "admin"
    supplier = "supplier"
    buyer = "buyer"

class UserCreate(BaseModel):
    email:EmailStr
    username:str
    role:UserRole=UserRole.buyer

class UserResponse(BaseModel):
    id:int
    email:EmailStr
    username:str
    role:UserRole

    model_config = {
        "from_attributes": True
    }
