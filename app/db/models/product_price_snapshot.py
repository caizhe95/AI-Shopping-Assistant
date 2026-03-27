from datetime import datetime 
from typing import Optional 
 
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, func 
from sqlalchemy.orm import Mapped, mapped_column, relationship 
 
from app.db.base import Base 
 
 
class ProductPriceSnapshot(Base): 
    __tablename__ = 'product_price_snapshots' 
 
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True) 
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id', ondelete='CASCADE'), nullable=False, index=True) 
    platform: Mapped[str] = mapped_column(String(64), nullable=False, default='', index=True) 
    seller_type: Mapped[str] = mapped_column(String(32), nullable=False, default='') 
    store_name: Mapped[str] = mapped_column(String(128), nullable=False, default='') 
    region: Mapped[str] = mapped_column(String(64), nullable=False, default='') 
    price_type: Mapped[str] = mapped_column(String(32), nullable=False, default='sale') 
    current_price: Mapped[float] = mapped_column(Float, nullable=False, default=0) 
    original_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True) 
    promotion_text: Mapped[str] = mapped_column(String(255), nullable=False, default='') 
    in_stock: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True) 
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True) 
    snapshot_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True) 
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True) 
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True) 
    currency: Mapped[str] = mapped_column(String(16), nullable=False, default='CNY') 
    note: Mapped[str] = mapped_column(String(255), nullable=False, default='') 
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now()) 
 
    product = relationship('Product', back_populates='price_snapshots')
