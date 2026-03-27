from __future__ import annotations 
 
import re 
from langchain_core.messages import SystemMessage 
 
def _text(value): 
    return str(value or '').strip() 
 
def trim_messages_window(messages, max_messages=8): 
    if not messages: 
        return [] 
    system_messages = [message for message in messages if isinstance(message, SystemMessage)] 
    other_messages = [message for message in messages if not isinstance(message, SystemMessage)] 
    trimmed = other_messages[-max_messages:] if max_messages else [] 
    return system_messages[:1] + trimmed 
 
def trim_steps_window(steps, max_steps=4): 
    if not steps: 
        return [] 
    trimmed = list(steps[-max_steps:]) if max_steps else list(steps) 
    return trimmed 
 
def merge_confirmed_facts(state): 
    facts = dict(state.get('confirmed_facts') or {}) 
    query = _text(state.get('user_query')) 
    if query and '预算' in query: 
        match = re.search(r'(\d+(?:\.\d+)?)', query) 
        if match: 
            facts['budget'] = match.group(1) 
    category_map = {'轻薄本': '轻薄本', '笔记本': '笔记本', '手机': '手机', '平板': '平板', '耳机': '耳机', '手表': '手表'} 
    for keyword, label in category_map.items(): 
        if keyword in query: 
            facts['category'] = label 
            break 
    if '自有品牌' in query: 
        facts['brand_preference'] = '自有品牌优先' 
    task_type = _text(state.get('task_type')) 
    if task_type: 
        facts['task_type'] = task_type 
    recommended = state.get('recommended_products') or [] 
    if recommended: 
        top_name = _text((recommended[0] or {}).get('name')) 
        if top_name: 
            facts['top_recommendation'] = top_name 
    detail = state.get('detail_result') or {} 
    if detail.get('name'): 
        facts['detail_product'] = _text(detail.get('name')) 
    price = state.get('price_context') or {} 
    if price.get('guide_price'): 
        facts['guide_price'] = price.get('guide_price') 
    state['confirmed_facts'] = facts 
    return facts 
 
def build_reasoning_summary(state): 
    facts = dict(state.get('confirmed_facts') or {}) 
    parts = [] 
    task_type = _text(state.get('task_type')) 
    if task_type: 
        parts.append('当前任务：' + task_type) 
    if facts.get('budget'): 
        parts.append('预算：' + _text(facts.get('budget'))) 
    if facts.get('category'): 
        parts.append('品类：' + _text(facts.get('category'))) 
    if facts.get('brand_preference'): 
        parts.append('品牌偏好：' + _text(facts.get('brand_preference'))) 
    done_actions = state.get('done_actions') or [] 
    if done_actions: 
        parts.append('已执行：' + '、'.join(done_actions[-4:])) 
    candidate_items = state.get('filtered_products') or state.get('retrieved_products') or state.get('comparison_candidates') or [] 
    if candidate_items: 
        names = [] 
        for item in candidate_items[:3]: 
            name = _text((item or {}).get('name')) 
            if name: 
                names.append(name) 
        if names: 
            parts.append('当前候选：' + '、'.join(names)) 
    summary = '；'.join(part for part in parts if part) 
    state['reasoning_summary'] = summary 
    return summary
