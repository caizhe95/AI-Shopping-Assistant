from datetime import datetime 
from typing import Any 
 
from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String, Text, func 
from sqlalchemy.orm import Mapped, mapped_column, relationship 
 
from app.db.base import Base 
 
 
class Product(Base): 
    __tablename__ = 'products' 
 
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True) 
    brand: Mapped[str] = mapped_column(String(64), nullable=False, index=True) 
    series: Mapped[str] = mapped_column(String(64), nullable=False, default='', index=True) 
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True) 
    category: Mapped[str] = mapped_column(String(64), nullable=False, default='smartphone') 
    sub_category: Mapped[str] = mapped_column(String(64), nullable=False, default='') 
    tagline: Mapped[str] = mapped_column(String(255), nullable=False, default='') 
    positioning: Mapped[str] = mapped_column(String(128), nullable=False, default='') 
    market_status: Mapped[str] = mapped_column(String(32), nullable=False, default='active') 
    is_own_brand: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True) 
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True) 
    guide_priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True) 
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True) 
    guide_price: Mapped[float] = mapped_column(Float, nullable=False, default=0) 
    price_min: Mapped[float] = mapped_column(Float, nullable=False, default=0) 
    price_max: Mapped[float] = mapped_column(Float, nullable=False, default=0) 
    target_users: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list) 
    usage_scenarios: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list) 
    selling_points: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list) 
    weaknesses: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list) 
    compare_scores: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict) 
    features: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list) 
    specs: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict) 
    description: Mapped[str] = mapped_column(Text, nullable=False, default='') 
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now()) 
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()) 
 
    price_snapshots = relationship('ProductPriceSnapshot', back_populates='product', cascade='all, delete-orphan')
