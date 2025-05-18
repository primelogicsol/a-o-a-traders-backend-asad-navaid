from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class ProductImageCreate(BaseModel):
    product_id: str 

class ProductImageUpdate(BaseModel):
    image_type: Optional[str] = None
    variant: Optional[str] = None
    url: Optional[str] = None 

class ProductImageRead(BaseModel):
    product_id: str

    main_image: Optional[str] = None
    image_variant1: Optional[str] = None
    image_variant2: Optional[str] = None
    image_variant3: Optional[str] = None
    image_variant4: Optional[str] = None
    image_variant5: Optional[str] = None
    alt_image: Optional[str] = None
    alt_image_variant1: Optional[str] = None
    alt_image_variant2: Optional[str] = None
    alt_image_variant3: Optional[str] = None
    brand_logo_image: Optional[str] = None
    brand_logo_image_url: Optional[str] = None
    msds_image: Optional[str] = None
    msds_image_url: Optional[str] = None

    model_config = {
        "from_attributes": True
    }
