from pydantic import BaseModel
from typing import List,Union

class CertificationResponse(BaseModel):
    id: int
    name: str
    issue_date: str

    model_config = {
        "from_attributes": True
    }


class ProductResponse(BaseModel):
    id: int
    name: str
    total_sales: int

    model_config = {
        "from_attributes": True
    }


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
    __root__: Union[SupplierDashboardResponse, AdminDashboardResponse]