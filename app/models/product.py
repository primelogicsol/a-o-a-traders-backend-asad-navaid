# models/product.py
import uuid
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, UUID, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class Product(Base):
    __tablename__ = "products"

    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(String,primary_key=True, nullable=False)  # Provided by vendor
    item_number=Column(String,unique=True)
    product_name = Column(String, index=True)
    price = Column(Float)
    description = Column(Text)
    brand = Column(Text)
    category = Column(String)
    stock_qty = Column(Integer)
    item_weight = Column(Float)
    keywords=Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    supplier = relationship("User", back_populates="products")

    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_supplier_product_id", "supplier_id", "product_id", unique=True),
    )
