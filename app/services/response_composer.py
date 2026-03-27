from __future__ import annotations


def _text(value):
    return str(value or '').strip()


def _names(items, limit=3):
    out = []
    for item in items or []:
        if not len(out) < limit:
            break
        name = _text((item or {}).get('name'))
        if name:
            out.append(name)
    return out


def _price_text(state):
    price = state.get('price_context') or {}
    parts = []
    if price.get('guide_price'):
        parts.append('导购价约 {} 元'.format(int(price['guide_price'])))
    if price.get('price_min') and price.get('price_max'):
        parts.append('价格区间约 {}-{} 元'.format(int(price['price_min']), int(price['price_max'])))
    if price.get('snapshot_count'):
        parts.append('已有 {} 条价格快照'.format(int(price['snapshot_count'])))
    return '，'.join(parts)


def _clarify(state):
    question = _text(state.get('clarification_question'))
    if question:
        return question
    return '请告诉我你的预算、品类或使用场景，我会继续帮你收缩选择。'


def _recommend(state):
    rec = state.get('recommendation_result') or {}
    items = rec.get('recommended_products') or rec.get('product_list') or state.get('recommended_products') or []
    top = rec.get('top_product') or (items[0] if items else {})
    parts = []
    if top.get('name'):
        parts.append('先给你结论：我更建议优先看 {}。'.format(top['name']))
    summary = _text(rec.get('summary') or state.get('final_response'))
    if summary:
        parts.append(summary)
    price = _price_text(state)
    if price:
        parts.append(price)
    backups = _names(items[1:4], limit=3)
    if backups:
        parts.append('如果你想再留几个备选，可以看：{}。'.format('、'.join(backups)))
    return ' '.join(parts).strip() or '推荐结果已经整理好了。'


def _compare(state):
    cmp = state.get('comparison_result') or {}
    items = cmp.get('product_list') or cmp.get('products') or cmp.get('comparison_candidates') or state.get('comparison_candidates') or []
    names = _names(items, limit=4)
    parts = []
    if names:
        parts.append('我已经把这几个商品放在一起对比：{}。'.format('、'.join(names)))
    summary = _text(cmp.get('summary') or state.get('final_response'))
    if summary:
        parts.append(summary)
    if names:
        parts.append('可以根据你更看重的性能、价格或日常体验来做取舍。')
    return ' '.join(parts).strip() or '对比结果已经整理好了。'


def _detail(state):
    detail = state.get('detail_result') or {}
    parts = []
    if detail.get('name'):
        parts.append('我帮你查到了 {} 的详细信息。'.format(detail['name']))
    price = _price_text(state)
    if price:
        parts.append(price)
    return ' '.join(parts).strip() or '详细信息已经补充好了。'


def _price_only(state):
    price = _price_text(state)
    if price:
        return '我帮你补到了价格信息：' + price + '。'
    return '还没有拿到明确的价格信息。'


def _search(state):
    items = state.get('filtered_products') or state.get('retrieved_products') or []
    names = _names(items, limit=4)
    if not names:
        return ''
    return '我先帮你筛到 {} 款，比较值得看的是：{}。'.format(len(items), '、'.join(names))


def compose_response(mode, state):
    state = state or {}
    task_type = _text(state.get('task_type') or mode or 'recommend')
    if state.get('clarification_question'):
        return _clarify(state)
    if task_type == 'recommend' and (state.get('recommendation_result') or state.get('recommended_products')):
        return _recommend(state)
    if task_type == 'compare' and (state.get('comparison_result') or state.get('comparison_candidates')):
        return _compare(state)
    if task_type == 'detail' and state.get('detail_result'):
        return _detail(state)
    if task_type == 'price' and state.get('price_context'):
        return _price_only(state)
    if state.get('recommendation_result') or state.get('recommended_products'):
        return _recommend(state)
    if state.get('comparison_result') or state.get('comparison_candidates'):
        return _compare(state)
    if state.get('detail_result'):
        return _detail(state)
    if state.get('price_context'):
        return _price_only(state)
    if state.get('filtered_products') or state.get('retrieved_products'):
        return _search(state) or _text(state.get('final_response'))
    final = _text(state.get('final_response'))
    if final:
        return final
    return '请告诉我你的预算、品类或使用场景，我会继续帮你收缩选择。'
