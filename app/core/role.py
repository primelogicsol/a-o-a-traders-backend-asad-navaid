from fastapi import Depends, HTTPException, status
from typing import Annotated
from app.services.jwt import get_current_user
from app.models.user import User

def role_required(*roles: str):
    async def _role_guard(user: Annotated[User, Depends(get_current_user)]):
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource."
            )
        return user
    return Depends(_role_guard)
