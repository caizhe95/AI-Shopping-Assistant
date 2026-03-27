from __future__ import annotations 
 
def _text(value): 
    return str(value or '').strip() 
 
def _trim_items(items, limit=3): 
    result = [] 
    for item in list(items or [])[:limit]: 
        if isinstance(item, dict): 
            result.append({'id': item.get('id'), 'name': item.get('name'), 'category': item.get('category'), 'price': item.get('price') or item.get('guide_price')}) 
        else: 
            result.append(item) 
    return result 
 
def normalize_observation(tool_name, raw_result): 
    if not isinstance(raw_result, dict): 
        return {'summary': _text(raw_result), 'data': {'value': raw_result}} 
    result = dict(raw_result) 
    data = dict(result.get('data') or {}) 
    if tool_name in ('search_products', 'filter_products'): 
        items = data.get('filtered_products') or data.get('retrieved_products') or data.get('product_list') or [] 
        data['items'] = _trim_items(items, limit=5) 
    elif tool_name == 'recommend_products': 
        items = data.get('recommended_products') or data.get('product_list') or [] 
        data['items'] = _trim_items(items, limit=3) 
    elif tool_name == 'compare_products': 
        products = data.get('products') or data.get('product_list') or [] 
        data['items'] = _trim_items(products, limit=4) 
        data['rows'] = list(data.get('rows') or [])[:6] 
    elif tool_name == 'get_product_detail': 
        detail = dict(data.get('detail_result') or data.get('product_detail') or {}) 
        if detail: 
            data['detail_result'] = {'id': detail.get('id'), 'name': detail.get('name'), 'category': detail.get('category'), 'price': detail.get('price') or detail.get('guide_price'), 'brand': detail.get('brand')} 
    elif tool_name == 'get_price_info': 
        price = dict(data.get('price_context') or data.get('price_result') or {}) 
        if price: 
            data['price_context'] = {'guide_price': price.get('guide_price'), 'current_price': price.get('current_price'), 'price_range': price.get('price_range'), 'snapshot_count': price.get('snapshot_count')} 
    result['data'] = data 
    return result 
 
def compress_observation(tool_name, result, max_chars=300): 
    if not isinstance(result, dict): 
        return _text(result)[:max_chars] 
    summary = _text(result.get('summary') or result.get('message') or result.get('final_response')) 
    if summary: 
        return summary[:max_chars] 
    data = result.get('data') or {} 
    if tool_name in ('search_products', 'filter_products', 'recommend_products'): 
        names = [str((item or {}).get('name') or '').strip() for item in list(data.get('items') or [])[:3] if str((item or {}).get('name') or '').strip()] 
        if names: 
            return ('候选商品：' + '、'.join(names))[:max_chars] 
    if tool_name == 'compare_products': 
        texts = [str((row or {}).get('result') or (row or {}).get('conclusion') or row or '').strip() for row in list(data.get('rows') or [])[:3] if str((row or {}).get('result') or (row or {}).get('conclusion') or row or '').strip()] 
        if texts: 
            return ('对比结论：' + '；'.join(texts))[:max_chars] 
    if tool_name == 'get_product_detail': 
        name = _text((data.get('detail_result') or {}).get('name')) 
        if name: 
            return ('已获取商品详情：' + name)[:max_chars] 
    if tool_name == 'get_price_info': 
        price = data.get('price_context') or {} 
        value = _text(price.get('guide_price') or price.get('current_price') or price.get('price_range')) 
        if value: 
            return ('已获取价格信息：' + value)[:max_chars] 
    return _text(result)[:max_chars]
