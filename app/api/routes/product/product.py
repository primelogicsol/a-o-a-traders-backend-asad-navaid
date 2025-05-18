from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func, and_, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Optional
from sqlalchemy import insert,update
from app.core.database import get_db
from app.models.product import Product
from app.models.product_image import ProductImage
from app.schemas.product.product import (
    ProductCreate, 
    ProductResponse,
    ProductUpdate,
    PaginatedProductResponse
)
from app.services.auth.jwt import get_current_user
from app.models.user import User

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
    current_user: User = Depends(get_current_user)
):

    from sqlalchemy import exists, select as subselect
    
    has_main_image = (
        subselect(1)
        .where(
            and_(
                ProductImage.product_id == Product.product_id,
                ProductImage.main_image.isnot(None)
            )
        )
        .exists()
        .label("has_main_image")
    )
    
    query = (
        select(Product)
        .join(ProductImage, Product.product_id == ProductImage.product_id)
        .where(
            and_(
                Product.is_active == True,
                Product.product_name.isnot(None),
                Product.price.isnot(None),
                ProductImage.main_image.isnot(None)
            )
        )
        .options(
            # Load all image data
            selectinload(Product.images)
        )
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
    
    query = query.order_by(Product.updated_at.desc()).offset((page - 1) * per_page).limit(per_page)
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
    current_user: User = Depends(get_current_user)
):

    query = (
        select(Product)
        .where(
            and_(
                Product.product_id == product_id,
                Product.is_active == True
            )
        )
        .options(
            selectinload(Product.images)
        )
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

@router.post("/", response_model=ProductResponse)
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = await db.execute(
        select(Product).where(Product.product_id == product.product_id)
    )
    if existing.scalar():
        raise HTTPException(status_code=400, detail="Product ID already exists")
    
    stmt = insert(Product).values(
        **product.model_dump(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    await db.execute(stmt)
    await db.commit()
    
    new_product = await db.execute(
        select(Product)
        .where(Product.product_id == product.product_id)
        .options(selectinload(Product.images))
    )
    return new_product.scalar()

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_update: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    
    existing = await db.execute(
        select(Product).where(Product.product_id == product_id)
    )
    if not existing.scalar():
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = product_update.model_dump(exclude_unset=True)
    update_data['updated_at'] = datetime.utcnow()
    
    stmt = (
        update(Product)
        .where(Product.product_id == product_id)
        .values(**update_data)
    )
    await db.execute(stmt)
    await db.commit()
    
    updated_product = await db.execute(
        select(Product)
        .where(Product.product_id == product_id)
        .options(selectinload(Product.images))
    )
    return updated_product.scalar()

@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = await db.execute(
        select(Product).where(Product.product_id == product_id)
    )
    if not existing.scalar():
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Soft delete
    stmt = (
        update(Product)
        .where(Product.product_id == product_id)
        .values(is_active=False, updated_at=datetime.utcnow())
    )
    await db.execute(stmt)
    await db.commit()
    
    return {"message": "Product deactivated successfully"}