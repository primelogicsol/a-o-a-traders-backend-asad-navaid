from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func, and_, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Optional
from app.core.database import get_db
from app.models.product import Product
from app.models.product_image import ProductImage
from app.schemas.product.product import (
    ProductResponse,
    PaginatedProductResponse
)

router = APIRouter()

@router.get("/", response_model=PaginatedProductResponse)
async def get_products(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Product)
        .join(ProductImage, Product.product_id == ProductImage.product_id, isouter=True)
        .where(Product.is_active == True)
        .options(selectinload(Product.images))
    )

    if search:
        query = query.where(
            Product.product_name.ilike(f"%{search}%") |
            Product.description.ilike(f"%{search}%") |
            Product.keywords.ilike(f"%{search}%")
        )
    if category:
        query = query.where(Product.category.ilike(f"%{category}%"))
    if min_price is not None:
        query = query.where(Product.price >= min_price)
    if max_price is not None:
        query = query.where(Product.price <= max_price)

    total_query = select(func.count()).select_from(query.alias())
    total = (await db.execute(total_query)).scalar()

    if total == 0:
        return {
            "items": [],
            "total": 0,
            "page": page,
            "pages": 0,
            "per_page": per_page
        }

    query = query.offset((page - 1) * per_page).limit(per_page)
    products = (await db.execute(query)).scalars().all()

    return {
        "items": products,
        "total": total,
        "page": page,
        "pages": (total + per_page - 1) // per_page,
        "per_page": per_page
    }


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Product)
        .where(
            and_(
                Product.product_id == product_id,
                Product.is_active == True
            )
        )
        .options(selectinload(Product.images))
    )
    
    result = await db.execute(query)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


