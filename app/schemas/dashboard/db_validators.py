from pydantic import BaseModel, ConfigDict
from typing import List, Union
from datetime import datetime  
from app.schemas.product.product import ProductResponse

class CertificationResponse(BaseModel):
    name: str
    issued_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,  
        json_encoders = {
            datetime: lambda v: v.isoformat()  
        }
    )


class SupplierDashboardResponse(BaseModel):
    total_products: int
    success_logs: int
    error_logs: int
    latest_certifications: List[CertificationResponse] 


class AdminDashboardResponse(BaseModel):
    total_users: int
    flagged_uploads: int
    top_selling_products: List[ProductResponse]  


class DashboardResponse(BaseModel):
    data: Union[SupplierDashboardResponse, AdminDashboardResponse]
    role: str  
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )