from __future__ import annotations 
from app.db.repositories.product_repository import ProductRepository 
CATEGORY_ALIASES = { 
    'laptop': ['laptop', '笔记本', '笔记本电脑', '轻薄本', '轻薄笔记本', '办公本'], 
    'smartphone': ['smartphone', '手机'], 
    'tablet': ['tablet', '平板', '平板电脑'], 
    'earbuds': ['earbuds', '耳机', '蓝牙耳机'], 
    'watch': ['watch', '手表', '智能手表'], 
} 
def _product_to_dict(product): 
 return { 
  'id': product.id, 
  'brand': product.brand, 
  'series': product.series, 
  'name': product.name, 
  'category': product.category, 
  'sub_category': product.sub_category, 
  'tagline': product.tagline, 
  'positioning': product.positioning, 
  'market_status': product.market_status, 
  'is_own_brand': product.is_own_brand, 
  'is_featured': product.is_featured, 
  'guide_priority': product.guide_priority, 
  'is_active': product.is_active, 
  'guide_price': float(product.guide_price or 0), 
  'price_min': float(product.price_min or product.guide_price or 0), 
  'price_max': float(product.price_max or product.guide_price or 0), 
  'target_users': product.target_users or [], 
  'usage_scenarios': product.usage_scenarios or [], 
  'selling_points': product.selling_points or [], 
  'weaknesses': product.weaknesses or [], 
  'compare_scores': product.compare_scores or {}, 
  'description': product.description, 
  'features': product.features or [], 
  'specs': product.specs or {}, 
 } 
 
def _price_snapshot_to_dict(price): 
 return { 
  'id': price.id, 
  'product_id': price.product_id, 
  'platform': price.platform, 
  'seller_type': price.seller_type, 
  'store_name': price.store_name, 
  'region': price.region, 
  'price_type': price.price_type, 
  'current_price': float(price.current_price or 0), 
  'original_price': float(price.original_price) if price.original_price is not None else None, 
  'promotion_text': price.promotion_text, 
  'in_stock': bool(price.in_stock), 
  'is_primary': bool(price.is_primary), 
  'snapshot_time': price.snapshot_time, 
  'valid_from': price.valid_from, 
  'valid_to': price.valid_to, 
  'currency': price.currency, 
  'note': price.note, 
  'created_at': price.created_at, 
 } 
def _build_price_summary(product_dict, snapshots): 
 min_snapshot = min((item['current_price'] for item in snapshots), default=product_dict['price_min']) 
 max_snapshot = max((item['current_price'] for item in snapshots), default=product_dict['price_max']) 
 currency = next((item['currency'] for item in snapshots if item.get('currency')), 'CNY') 
 return { 
  'guide_price': product_dict['guide_price'], 
  'price_min': product_dict['price_min'], 
  'price_max': product_dict['price_max'], 
  'min_price': float(min_snapshot or product_dict['price_min'] or product_dict['guide_price']), 
  'max_price': float(max_snapshot or product_dict['price_max'] or product_dict['guide_price']), 
  'currency': currency, 
  'snapshot_count': len(snapshots), 
 } 
def _expand_queries(query): 
 text = str(query or '').strip() 
 if not text: 
  return [''] 
 out = [] 
 seen = set() 
 lower_text = text.lower() 
 def add(value): 
  value = str(value or '').strip() 
  if value and value not in seen: 
   seen.add(value) 
   out.append(value) 
 add(text) 
 
 for base, aliases in CATEGORY_ALIASES.items(): 
  if any(alias.lower() in lower_text for alias in aliases): 
   add(base) 
   for alias in aliases: 
    add(alias) 
 for token in text.replace('，', ' ').replace('。', ' ').replace(',', ' ').split(): 
  add(token) 
 return out 
class ProductService: 
 def __init__(self, session): 
  self.repo = ProductRepository(session) 
 def build_search_summary(self, products, query=None): 
  query_text = str(query or '').strip() 
  if not products: 
   return '暂时没有找到匹配的商品，你可以补充预算、品类或使用场景。' 
  names = '、'.join(str(item.get('name') or '') for item in products[:3]) 
  if query_text: 
   return f'已找到 {len(products)} 个候选商品：{names}。' 
  return f'已召回 {len(products)} 个商品：{names}。' 
 async def search_products(self, query=None, limit=10): 
  merged = [] 
  seen_ids = set() 
  for keyword in _expand_queries(query): 
   products = await self.repo.search(keyword or None, limit=max(limit, 8)) 
   for product in products: 
    if product.id in seen_ids: 
     continue 
    seen_ids.add(product.id) 
    merged.append(product) 
    if not len(merged) < limit: 
     return [_product_to_dict(item) for item in merged[:limit]] 
  return [_product_to_dict(item) for item in merged[:limit]] 
 async def get_product_detail(self, product_id): 
  product = await self.repo.get_by_id(product_id) 
  if not product: 
   return None 
  snapshots = [_price_snapshot_to_dict(price) for price in await self.repo.get_price_snapshots(product_id)] 
  product_dict = _product_to_dict(product) 
  price_summary = _build_price_summary(product_dict, snapshots) 
  return {**product_dict, 'product': product_dict, 'detail_result': product_dict, 'price_context': price_summary, 'price_summary': price_summary, 'price_snapshots': snapshots} 
 
 async def get_price_info(self, product_id): 
  detail = await self.get_product_detail(product_id) 
  if not detail: 
   return None 
  return {'product_id': product_id, 'guide_price': detail.get('guide_price', 0), 'price_min': detail.get('price_min', 0), 'price_max': detail.get('price_max', 0), 'price_summary': detail.get('price_summary') or {}, 'price_snapshots': detail.get('price_snapshots') or [], 'price_context': detail.get('price_summary') or {}, 'summary': '已获取价格信息。'} 
 async def get_main_product(self): 
  product = await self.repo.get_main_product() 
  return _product_to_dict(product) if product else None 
 async def list_active_products(self, limit=20, offset=0): 
  products = await self.repo.list_active(limit=limit, offset=offset) 
  return [_product_to_dict(product) for product in products] 
