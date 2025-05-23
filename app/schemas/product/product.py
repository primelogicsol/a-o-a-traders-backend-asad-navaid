from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.schemas.product.images import ProductImageRead

class ProductBase(BaseModel):
    supplier_id: int
    product_id: str
    product_name: str
    description: Optional[str] = None
    price: Optional[float] = None
    brand: Optional[str] = None
    category: Optional[str] = None

class ProductCreate(ProductBase):
    supplier_id: int

class ProductUpdate(BaseModel):
    product_name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock_qty: Optional[int] = None
    is_active: Optional[bool] = True



class ProductResponse(ProductBase):
    stock_qty: Optional[int] = None
    item_weight: Optional[float] = None
    keywords: Optional[str] = None
    is_active: bool = True
    images: List[ProductImageRead] = [] 

    model_config = {
        "from_attributes": True
    }


class PaginatedProductResponse(BaseModel):
    items: List[ProductResponse]
    total: int
    page: int
    pages: int
    per_page: int