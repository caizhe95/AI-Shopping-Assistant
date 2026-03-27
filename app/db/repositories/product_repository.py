from __future__ import annotations 
 
from collections.abc import Sequence 
 
from sqlalchemy import String, cast, func, or_, select 
from sqlalchemy.ext.asyncio import AsyncSession 
 
from app.db.models.product_price_snapshot import ProductPriceSnapshot 
from app.db.models.product import Product 
 
 
class ProductRepository: 
    def __init__(self, session: AsyncSession): 
        self.session = session 
 
    def _default_ordering(self): 
        return ( 
            Product.is_own_brand.desc(), 
            Product.is_featured.desc(), 
            Product.guide_priority.desc(), 
            Product.guide_price.asc(), 
            Product.id.asc(), 
        ) 
 
    async def get_main_product(self): 
        featured_stmt = ( 
            select(Product) 
            .where(Product.is_active.is_(True), Product.is_own_brand.is_(True), Product.is_featured.is_(True)) 
            .order_by(Product.guide_priority.desc(), Product.guide_price.asc(), Product.id.asc()) 
        ) 
        product = await self.session.scalar(featured_stmt) 
        if product is not None: 
            return product 
        fallback_stmt = select(Product).where(Product.is_active.is_(True)).order_by(*self._default_ordering()) 
        return await self.session.scalar(fallback_stmt) 
 
    async def get_by_id(self, product_id: int): 
        return await self.session.get(Product, product_id) 
 
    async def get_by_ids(self, product_ids: Sequence[int]): 
        if not product_ids: 
            return [] 
        stmt = select(Product).where(Product.id.in_(list(product_ids)), Product.is_active.is_(True)).order_by(*self._default_ordering()) 
        result = await self.session.scalars(stmt) 
        return list(result.all())
 
    async def list_active(self, limit: int = 20, offset: int = 0): 
        stmt = ( 
            select(Product) 
            .where(Product.is_active.is_(True)) 
            .order_by(Product.guide_priority.desc(), Product.guide_price.asc(), Product.id.asc()) 
            .limit(limit) 
            .offset(offset) 
        ) 
        result = await self.session.scalars(stmt) 
        return list(result.all()) 
 
    async def search(self, keyword: str = None, limit: int = 10): 
        stmt = select(Product).where(Product.is_active.is_(True)) 
        if keyword: 
            kw = '%%' + keyword.strip() + '%%' 
            json_text_filters = ( 
                cast(Product.target_users, String).like(kw), 
                cast(Product.usage_scenarios, String).like(kw), 
                cast(Product.selling_points, String).like(kw),
                cast(Product.features, String).like(kw),
                cast(Product.specs, String).like(kw), 
            ) 
            stmt = stmt.where(or_( 
                Product.name.like(kw), 
                Product.brand.like(kw),
                Product.series.like(kw),
                Product.category.like(kw),
                Product.market_status.like(kw), 
                Product.tagline.like(kw), 
                Product.positioning.like(kw), 
                Product.description.like(kw), 
                Product.sub_category.like(kw), 
                *json_text_filters, 
            )) 
        stmt = stmt.order_by(*self._default_ordering()).limit(limit) 
        result = await self.session.scalars(stmt) 
        return list(result.all())
 
    async def get_price_snapshots(self, product_id: int): 
        stmt = ( 
            select(ProductPriceSnapshot) 
            .where(ProductPriceSnapshot.product_id == product_id) 
            .order_by(ProductPriceSnapshot.is_primary.desc(), ProductPriceSnapshot.current_price.asc(), ProductPriceSnapshot.snapshot_time.desc()) 
        ) 
        result = await self.session.scalars(stmt) 
        return list(result.all()) 
 
    async def get_price_stats(self, product_id: int): 
        stmt = select( 
            func.min(ProductPriceSnapshot.current_price), 
            func.max(ProductPriceSnapshot.current_price), 
            func.avg(ProductPriceSnapshot.current_price), 
            func.count(ProductPriceSnapshot.id), 
        ).where(ProductPriceSnapshot.product_id == product_id) 
        row = (await self.session.execute(stmt)).one() 
        return { 
            'min_price': float(row[0] or 0), 
            'max_price': float(row[1] or 0), 
            'avg_price': float(row[2] or 0), 
            'count': int(row[3] or 0), 
        }
