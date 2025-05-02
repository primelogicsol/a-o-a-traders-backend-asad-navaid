from pydantic import BaseModel,EmailStr,field_validator,ValidationInfo
from enum import Enum
from app.models.user import UserRole

class StandardResponse(BaseModel):
    success: bool
    message: str

class SetUserRoleRequest(BaseModel):
    email: str
    role: str

class UserCreate(BaseModel):
    email:EmailStr
    username:str
    password:str
    confirm_password:str

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, confirm_password_value: str, info: ValidationInfo) -> str:
        password_value = info.data.get("password")
        if password_value and password_value != confirm_password_value:
            raise ValueError("Passwords do not match")
        return confirm_password_value

class UserResponse(BaseModel):
    id:int
    email:EmailStr
    username:str
    role:UserRole

    model_config = {
        "from_attributes": True
    }
