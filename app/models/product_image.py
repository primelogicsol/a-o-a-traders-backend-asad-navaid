from sqlalchemy import Column, String, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base

class ProductImage(Base):
    __tablename__ = "product_images"

    product_id = Column(String, ForeignKey("products.product_id"), primary_key=True)

    main_image = Column(String, nullable=True)
    image_variant1 = Column(String, nullable=True)
    image_variant2 = Column(String, nullable=True)
    image_variant3 = Column(String, nullable=True)
    image_variant4 = Column(String, nullable=True)
    image_variant5 = Column(String, nullable=True)

    alt_image = Column(String, nullable=True)
    alt_image_variant1 = Column(String, nullable=True)
    alt_image_variant2 = Column(String, nullable=True)
    alt_image_variant3 = Column(String, nullable=True)

    brand_logo_image = Column(String, nullable=True)
    brand_logo_image_url = Column(String, nullable=True)

    msds_image = Column(String, nullable=True)
    msds_image_url = Column(String, nullable=True)

    product = relationship("Product", back_populates="images")

