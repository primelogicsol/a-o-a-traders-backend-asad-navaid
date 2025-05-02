from pydantic import BaseModel
from typing import Optional
from datetime import date

class ProductSchema(BaseModel):
    part_number: Optional[str]
    your_part_number: Optional[str]
    item_description: str
    brand_name: str
    vendor_part_number: Optional[str]
    vendor_name: str
    product_category: str
    product_subcategory: str
    upc_code: str
    min_order_qty: int
    min_order_uom: str
    uom_conversion: str
    cost_uom: str
    std_pkg_list_price: float
    std_pkg_cust_cost: float
    price_date: date
    item_weight: float
    item_height: float
    item_width: float
    item_length: float
    item_cube: float
    country_of_origin: Optional[str]
    hazmat_item: Optional[bool] = False
    special_order_item: Optional[bool] = False
    state_restricted: Optional[bool] = False
    recno: Optional[int]
    temp_price: Optional[float]
    promo_price: Optional[float]
    promo_start_date: Optional[date]
    promo_end_date: Optional[date]
    kf: Optional[str]

    model_config = {
        "from_attributes": True
    }
