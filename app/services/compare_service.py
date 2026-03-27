from app.db.repositories.product_repository import ProductRepository 
from app.services.product_service import _product_to_dict 
METRIC_LABELS = { 
    'performance': '性能', 
    'camera': '拍照', 
    'battery': '续航', 
    'screen': '屏幕', 
    'portability': '便携性', 
} 
class CompareService: 
    def __init__(self, session): 
        self.repo = ProductRepository(session) 
    def _score_value(self, product, key): 
        scores = product.get('compare_scores') or {} 
        value = scores.get(key) 
        if isinstance(value, (int, float)): 
            return float(value) 
        if isinstance(value, str): 
            mapping = {'low': 1.0, 'entry': 1.0, 'mid': 2.0, 'medium': 2.0, 'high': 3.0, 'strong': 3.0, 'top': 4.0, 'flagship': 4.0} 
            text = value.strip().lower() 
            if text in mapping: 
                return mapping[text] 
        legacy = product.get('specs', {}).get(key) 
        if isinstance(legacy, (int, float)): 
            return float(legacy) 
        return None 
    def _metric_comment(self, base, other, key, label): 
        left = self._score_value(base, key) 
        right = self._score_value(other, key) 
        if left is None or right is None: 
            return label + '相当' 
        diff = left - right 
        if diff > 0.6: 
            return base['name'] + '在' + label + '方面更强' 
        if diff < -0.6: 
            return other['name'] + '在' + label + '方面更强' 
        return label + '相当' 
 
    def _price_comment(self, base, other): 
        primary_price = float(base.get('guide_price') or base.get('price_min') or 0) 
        other_price = float(other.get('guide_price') or other.get('price_min') or 0) 
        if not primary_price or not other_price: 
            return '价格接近' 
        diff = primary_price - other_price 
        if abs(diff) <= max(primary_price, other_price) * 0.08: 
            return '价格接近' 
        if diff < 0: 
            return base['name'] + '价格更低' 
        return other['name'] + '价格更低' 
    async def compare_products(self, product_ids): 
        products = await self.repo.get_by_ids(product_ids) 
        items = [_product_to_dict(product) for product in products] 
        if not items or len(items) == 1: 
            return {'product_list': items, 'products': items, 'comparison_candidates': items, 'comparison_rows': [], 'rows': [], 'summary': '商品数量不足，无法对比'} 
        base = items[0] 
        rows = [] 
        for other in items[1:]: 
            rows.append({ 
                'left_product': base['name'], 
                'right_product': other['name'], 
                '性能': self._metric_comment(base, other, 'performance', METRIC_LABELS['performance']), 
                '拍照': self._metric_comment(base, other, 'camera', METRIC_LABELS['camera']), 
                '续航': self._metric_comment(base, other, 'battery', METRIC_LABELS['battery']), 
                '屏幕': self._metric_comment(base, other, 'screen', METRIC_LABELS['screen']), 
                '便携性': self._metric_comment(base, other, 'portability', METRIC_LABELS['portability']), 
                '价格': self._price_comment(base, other), 
            }) 
        summary = '对比完成：' + base['name'] + ' 对 比 ' + '、'.join(item['name'] for item in items[1:]) 
        return {'product_list': items, 'products': items, 'comparison_candidates': items, 'comparison_rows': rows, 'rows': rows, 'summary': summary} 
