from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User



async def supplier_db(db:AsyncSession,user:User):
    total_products=await db.execute(select(func.count(Product.id)).where(Product.supplier_id==user.id))



    