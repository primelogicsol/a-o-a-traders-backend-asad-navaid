from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User
from app.schemas.dashboard.db_validators import DashboardResponse, SupplierDashboardResponse, AdminDashboardResponse
from app.services.dashboard.db_details import get_supplier_data, get_admin_data
from app.core.role import role_required
from app.utils.exportcsv import generate_csv

router = APIRouter()

@router.get("/details/", response_model=DashboardResponse)
async def get_dashboard(
    current_user: User = Depends(role_required(["supplier", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role == "supplier":
        data = await get_supplier_data(current_user.id, db)
        return DashboardResponse(data=SupplierDashboardResponse(**data), role="supplier")

    elif current_user.role == "admin":
        data = await get_admin_data(db)
        return DashboardResponse(data=AdminDashboardResponse(**data), role="admin")

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


@router.get("/stats/supplier/export")
async def export_supplier_stats(user_id: int, db: AsyncSession = Depends(get_db),current_user: User = Depends(role_required("supplier"))):
    stats = await get_supplier_data(user_id, db)
    header = ["Metric", "Value"]
    data = [
        ["Total Products", stats["total_products"]],
        ["Successful Uploads", stats["success_logs"]],
        ["Error Uploads", stats["error_logs"]],
    ]

    data.append([])  
    data.append(["Latest Certifications"])
    data.append(["Name", "Issued At"])
    for cert in stats["latest_certifications"]:
        data.append([cert["name"], cert["issued_at"]])

    return generate_csv(data, header, "supplier_stats.csv")

@router.get("/stats/admin/export")
async def export_admin_stats(db: AsyncSession = Depends(get_db),current_user: User = Depends(role_required("admin"))):
    stats = await get_admin_data(db)
    header = ["Metric", "Value"]
    data = [
        ["Total Users", stats["total_users"]],
        ["Flagged Uploads", stats["flagged_uploads"]],
    ]

    data.append([]) 
    data.append(["Top Selling Products"])
    data.append(["Product Name", "Units Sold"])
    for product in stats["top_selling_products"]:
        data.append([product["name"], product["units_sold"]])

    return generate_csv(data, header, "admin_stats.csv")
