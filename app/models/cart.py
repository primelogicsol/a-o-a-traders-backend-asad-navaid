from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class CartItem(Base):

    __tablename__="cart_items"

    id=Column(Integer,primary_key=True,index=True)
    buyer_id=Column(Integer,ForeignKey("user.id",ondelete="CASCADE"))
    product_id=Column(Integer,ForeignKey("products.id",ondelete="CASCADE"))
    quantity=Column(Integer,default=1)

    buyer=relationship("User",back_populates="cart")
    product=relationship("Product")

    __table_args__ = (UniqueConstraint("buyer_id", "product_id", name="uix_cartitem"),)


class WishlistItem(Base):
    __tablename__ = "wishlist_items"
    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))

    buyer = relationship("User", back_populates="wishlist")
    product = relationship("Product")
    

    __table_args__ = (UniqueConstraint("buyer_id", "product_id", name="uix_wishlistitem"),)

