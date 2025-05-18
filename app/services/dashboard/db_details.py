from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.models.product import Product
from app.models.user import User
from app.models.supplier_details import UploadLog,Certification

async def get_supplier_data(
        user_id:int,db:AsyncSession
):
    counts=await db.execute(
        select(
            select(func.count()).where(Product.supplier_id==user_id).select_from(Product).scalar_subquery().label("total_products"),
            select(func.count()).where(
                UploadLog.supplier_id == user_id,
                UploadLog.status == "error"
            ).select_from(UploadLog).scalar_subquery().label("error_logs"),
            select(func.count()).where(
                UploadLog.supplier_id == user_id,
                UploadLog.status == "success"
            ).select_from(UploadLog).scalar_subquery().label("success_logs"),
        )
    )
    count_row = counts.fetchone()

    recent_certifications=await db.execute(select(Certification.name,Certification.issued_at)
        .where(Certification.supplier_id == user_id)
        .order_by(desc(Certification.issued_at))
        .limit(5)
    )

    return {
        "total_products": count_row.total_products or 0,
        "success_logs": count_row.success_logs or 0,
        "error_logs": count_row.error_logs or 0,
        "latest_certifications": recent_certifications.mappings().all()
    }


async def get_admin_data(db: AsyncSession):
    counts = await db.execute(
        select(
            select(func.count()).select_from(User).scalar_subquery().label("total_users"),
            select(func.count()).where(UploadLog.status == "flagged")
                .select_from(UploadLog).scalar_subquery().label("flagged_uploads"),
        )
    )
    count_row = counts.fetchone()

    top_selling_products = await db.execute(
        select(Product.name, Product.units_sold)
        .order_by(desc(Product.units_sold))
        .limit(5)
    )

    return {
        "total_users": count_row.total_users or 0,
        "flagged_uploads": count_row.flagged_uploads or 0,
        "top_selling_products": top_selling_products.mappings().all()
    }
        
    
