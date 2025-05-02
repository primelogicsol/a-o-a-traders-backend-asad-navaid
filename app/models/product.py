from sqlalchemy import Column, Integer, String, Float, Boolean, Date,ForeignKey
from app.core.database import Base
from sqlalchemy.orm import relationship

class Product(Base):
    __tablename__ = "products"


    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    id = Column(Integer, primary_key=True, index=True)
    part_number = Column(String, nullable=True)
    your_part_number = Column(String, nullable=True)
    item_description = Column(String)
    brand_name = Column(String)
    vendor_part_number = Column(String, nullable=True)
    vendor_name = Column(String)
    product_category = Column(String)
    product_subcategory = Column(String)
    upc_code = Column(String)
    min_order_qty = Column(Integer)
    min_order_uom = Column(String)
    uom_conversion = Column(String)
    cost_uom = Column(String)
    std_pkg_list_price = Column(Float)
    std_pkg_cust_cost = Column(Float)
    price_date = Column(Date)
    item_weight = Column(Float)
    item_height = Column(Float)
    item_width = Column(Float)
    item_length = Column(Float)
    item_cube = Column(Float)
    country_of_origin = Column(String)
    hazmat_item = Column(Boolean, default=False)
    special_order_item = Column(Boolean, default=False)
    state_restricted = Column(Boolean, default=False)
    recno = Column(Integer, nullable=True)
    temp_price = Column(Float, nullable=True)
    promo_price = Column(Float, nullable=True)
    promo_start_date = Column(Date, nullable=True)
    promo_end_date = Column(Date, nullable=True)
    kf = Column(String, nullable=True)
    
    supplier = relationship("User", back_populates="products")