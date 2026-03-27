from __future__ import annotations 
 
import re 
 
from app.db.repositories.product_repository import ProductRepository 
from app.services.product_service import _product_to_dict 
 
def _normalize_text(value): 
    return str(value or '').lower() 
 
def _extract_budget(query): 
    match = re.search(r'(\d+(?:\.\d+)?)', str(query or '')) 
    return float(match.group(1)) if match else None 
 
def _tokenize(text): 
    return [token for token in re.split(r'\W+', _normalize_text(text)) if len(token) >= 2] 
 
def _combined_text(product): 
    parts = [product.get('brand'), product.get('series'), product.get('name'), product.get('category'), product.get('sub_category'), product.get('tagline'), product.get('positioning'), product.get('description')] 
    parts.extend(product.get('target_users') or []) 
    parts.extend(product.get('usage_scenarios') or []) 
    parts.extend(product.get('selling_points') or []) 
    parts.extend(product.get('features') or []) 
    return ' '.join(str(part or '') for part in parts).lower() 
 
def _budget_score(product, budget): 
    price = float(product.get('guide_price') or 0) 
    low = float(product.get('price_min') or price or 0) 
    high = float(product.get('price_max') or price or low) 
    if not budget or budget <= 0: 
        return 0.06, '价格约 ' + str(int(price or 0)) 
    if low <= budget <= max(high, low): 
        return 0.30, '价格符合预算区间' 
    if low > budget: 
        return 0.10, '价格略高于预算' 
    return 0.12, '价格略低于预算' 
 
def _score_product(product, query, budget): 
    score = 0.0 
    reasons = [] 
    combined = _combined_text(product) 
    matched = [token for token in _tokenize(query) if token in combined] 
    if matched: 
        score += min(0.34, 0.08 * len(matched)) 
        reasons.append('整体需求匹配度高') 
    selling_points = product.get('selling_points') or [] 
    if selling_points: 
        reasons.append(str(selling_points[0])) 
        score += 0.06 
    price_score, price_reason = _budget_score(product, budget) 
    score += price_score 
    reasons.append(price_reason) 
    if product.get('is_own_brand'): 
        score += 0.14 
        reasons.append(str(product.get('brand') or '自有品牌') + ' 机型') 
    if product.get('is_featured'): 
        score += 0.12 
        reasons.append('重点推荐') 
    score += min(0.12, max(0, int(product.get('guide_priority') or 0)) * 0.02) 
    tagline = str(product.get('tagline') or '').strip() 
    if tagline: 
        reasons.append(tagline) 
    unique_reasons = [] 
    for reason in reasons: 
        cleaned = str(reason or '').strip() 
        if cleaned and cleaned not in unique_reasons: 
            unique_reasons.append(cleaned) 
    return round(score, 3), unique_reasons[:4] 
 
def _build_result(query, budget, recommendations, compare_needed, compare_product_ids, comparison_candidates, summary, top_product): 
    return {'query': query, 'budget': budget, 'recommended_products': recommendations, 'product_list': recommendations, 'top_product': top_product or {}, 'compare_needed': compare_needed, 'compare_product_ids': compare_product_ids, 'comparison_candidates': comparison_candidates, 'summary': summary} 
 
class RecommendService: 
    def __init__(self, session): 
        self.repo = ProductRepository(session) 
 
    async def recommend_products(self, query='', candidate_ids=None, limit=5): 
        query = str(query or '') 
        candidate_ids = list(candidate_ids or []) 
        if candidate_ids: 
            products = await self.repo.get_by_ids(candidate_ids) 
        elif query.strip(): 
            products = await self.repo.search(query, limit=max(limit * 3, 12)) 
        else: 
            products = await self.repo.list_active(limit=max(limit * 3, 12)) 
        items = [_product_to_dict(product) for product in products] 
        budget = _extract_budget(query) 
        if not items: 
            return _build_result(query, budget, [], False, [], [], '没有找到合适的商品。', {}) 
        ranked = [] 
        for item in items: 
            score, reasons = _score_product(item, query, budget) 
            ranked.append({**item, 'score': score, 'reasons': reasons}) 
        ranked.sort(key=lambda item: (-item['score'], not item['is_own_brand'], not item['is_featured'], item['guide_price'])) 
        recommendations = ranked[:limit] 
        picked_ids = {item['id'] for item in recommendations} 
        alternatives = [item for item in ranked if item['id'] not in picked_ids] 
        compare_product_ids = [item['id'] for item in alternatives[:3]] 
        compare_needed = any(keyword in _normalize_text(query) for keyword in ["对比", "比较", "差异", "区别", "哪个好", "vs", "versus"]) and bool(compare_product_ids)
        top = recommendations[0] 
        summary_parts = ['首推 ' + str(top.get('name') or '')] 
        if budget: 
            summary_parts.append('预算约 ' + str(int(budget))) 
        if top.get('is_own_brand'): 
            summary_parts.append('自有品牌优先') 
        if top.get('is_featured'): 
            summary_parts.append('重点推荐') 
        if compare_needed: 
            summary_parts.append('如需对比可继续查看备选') 
        return _build_result(query, budget, recommendations, compare_needed, compare_product_ids, alternatives[:3], '; '.join(summary_parts), top) 
