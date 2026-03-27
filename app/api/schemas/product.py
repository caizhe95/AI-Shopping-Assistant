from datetime import datetime  
from typing import Any, Optional  
  
from pydantic import BaseModel, ConfigDict, Field  
  
  
class ProductPriceSnapshotSchema(BaseModel):  
    model_config = ConfigDict(from_attributes=True, extra='ignore')  
  
    id: int  
    product_id: int  
    platform: str = ''  
    seller_type: str = ''  
    store_name: str = ''  
    region: str = ''  
    price_type: str = 'sale'  
    current_price: float = 0  
    original_price: Optional[float] = None  
    promotion_text: str = ''  
    in_stock: bool = True  
    is_primary: bool = False  
    snapshot_time: Optional[datetime] = None  
    valid_from: Optional[datetime] = None  
    valid_to: Optional[datetime] = None  
    currency: str = 'CNY'  
    note: str = ''  
    created_at: Optional[datetime] = None  
  
  
class ProductPriceSummary(BaseModel):  
    model_config = ConfigDict(extra='ignore')  
  
    guide_price: float = 0  
    price_min: float = 0  
    price_max: float = 0  
    min_price: float = 0  
    max_price: float = 0  
    currency: str = 'CNY'  
    snapshot_count: int = 0 
  
  
class ProductBaseSchema(BaseModel):  
    model_config = ConfigDict(from_attributes=True, extra='ignore')  
  
    id: int  
    brand: str  
    series: str = ''  
    name: str  
    category: str = ''  
    sub_category: str = ''  
    tagline: str = ''  
    positioning: str = ''  
    market_status: str = 'active'  
    is_own_brand: bool = False  
    is_featured: bool = False  
    guide_priority: int = 0  
    is_active: bool = True  
    guide_price: float = 0  
    price_min: float = 0  
    price_max: float = 0  
    target_users: list[str] = Field(default_factory=list)  
    usage_scenarios: list[str] = Field(default_factory=list)  
    selling_points: list[str] = Field(default_factory=list)  
    weaknesses: list[str] = Field(default_factory=list)  
    compare_scores: dict[str, Any] = Field(default_factory=dict)  
    features: list[str] = Field(default_factory=list)  
    specs: dict[str, Any] = Field(default_factory=dict)  
    description: str = ''
    created_at: Optional[datetime] = None  
    updated_at: Optional[datetime] = None  
  
  
class ProductBrief(ProductBaseSchema):  
    pass  
  
  
class ProductDetail(ProductBaseSchema):  
    price_summary: ProductPriceSummary = Field(default_factory=ProductPriceSummary)  
    price_snapshots: list[ProductPriceSnapshotSchema] = Field(default_factory=list)  
  
  
class ProductListResponse(BaseModel):  
    model_config = ConfigDict(extra='ignore')  
  
    items: list[ProductBrief] = Field(default_factory=list)  
  
  
class ProductUpsert(BaseModel):  
    model_config = ConfigDict(extra='ignore')  
  
    brand: str  
    series: str = ''  
    name: str  
    category: str = ''  
    sub_category: str = ''  
    tagline: str = ''  
    positioning: str = ''  
    market_status: str = 'active'  
    is_own_brand: bool = False  
    is_featured: bool = False  
    guide_priority: int = 0  
    is_active: bool = True  
    guide_price: float = 0  
    price_min: float = 0  
    price_max: float = 0  
    target_users: list[str] = Field(default_factory=list)  
    usage_scenarios: list[str] = Field(default_factory=list)  
    selling_points: list[str] = Field(default_factory=list)  
    weaknesses: list[str] = Field(default_factory=list)  
    compare_scores: dict[str, Any] = Field(default_factory=dict)  
    features: list[str] = Field(default_factory=list)  
    specs: dict[str, Any] = Field(default_factory=dict)  
    description: str = ''
