from fastapi import APIRouter, Depends,HTTPException
from app.schemas.dashboard.db_validators import DashboardResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db 
from app.models.user import User
from app.services.auth.jwt import get_current_user

router=APIRouter()


@router.get("/dashboard",response_model=DashboardResponse)
async def getdashboard_data(current_user:User=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    if current_user.role=="supplier":
        pass
    elif current_user.role=="admin":
        pass
    else:
        raise HTTPException(status_code=403, detail="Unauthorized access.")
