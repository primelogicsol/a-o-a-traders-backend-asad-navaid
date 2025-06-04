from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Optional
from app.core.database import get_db
from app.core.role import role_required
from app.models.product import Product
from app.models.product_image import ProductImage
from app.schemas.product.product import (
    ProductResponse,
    PaginatedProductResponse
)
from app.models.user import User

router = APIRouter()

from sqlalchemy.orm import joinedload, contains_eager

@router.get("/", response_model=PaginatedProductResponse)
async def get_products(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required("supplier"))
):

    query = (
        select(Product)
        .outerjoin(ProductImage, Product.product_id == ProductImage.product_id)
        .where(Product.supplier_id == current_user.id)
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

    total_query = select(func.count()).select_from(query.subquery())
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
    current_user: User = Depends(role_required("supplier"))
):
    query = (
        select(Product)
        .where(
            and_(
                Product.product_id == product_id,
                Product.is_active == True,
                Product.supplier_id == current_user.id  # restrict to current supplier
            )
        )
        .options(selectinload(Product.images))
    )
    
    result = await db.execute(query)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    has_images = product.images and any(img.main_image for img in product.images)
    
    if not product.product_name or not product.price or not has_images:
        raise HTTPException(
            status_code=404, 
            detail="Product does not have complete data"
        )
    
    return product


@router.delete("/all", summary="Hard delete all products of the current supplier")
async def hard_delete_all_products(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required("supplier"))
):

    product_ids_result = await db.execute(
        select(Product.product_id).where(Product.supplier_id == current_user.id)
    )
    product_ids = [row[0] for row in product_ids_result.fetchall()]

    if not product_ids:
        return {"message": "No products found for this supplier."}

    await db.execute(
        ProductImage.__table__.delete().where(ProductImage.product_id.in_(product_ids))
    )

    await db.execute(
        Product.__table__.delete().where(Product.product_id.in_(product_ids))
    )

    await db.commit()
    return {"message": f"All {len(product_ids)} products have been permanently deleted."}


@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required("supplier"))
):
    existing = await db.execute(
        select(Product).where(
            and_(
                Product.product_id == product_id,
                Product.supplier_id == current_user.id  
            )
        )
    )
    product = existing.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Soft delete
    stmt = (
        update(Product)
        .where(Product.product_id == product_id)
        .values(is_active=False)
    )
    await db.execute(stmt)
    await db.commit()
    
    return {"message": "Product deactivated successfully"}
