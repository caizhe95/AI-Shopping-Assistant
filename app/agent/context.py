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
    return system_messages[:1] + list(other_messages) 
 
def trim_steps_window(steps, max_steps=4): 
    if not steps: 
        return [] 
    trimmed = list(steps[-max_steps:]) if max_steps else list(steps) 
    return trimmed 
 
def merge_confirmed_facts(state): 
    facts = dict(state.get('confirmed_facts') or {}) 
    query = _text(state.get('user_query')) 
    if query and '\u9884\u7b97' in query: 
        match = re.search(r'(\d+(?:\.\d+)?)', query) 
        if match: 
            facts['budget'] = match.group(1) 
    category_map = {'\u8f7b\u8584\u672c': '\u8f7b\u8584\u672c', '\u7b14\u8bb0\u672c': '\u7b14\u8bb0\u672c', '\u624b\u673a': '\u624b\u673a', '\u5e73\u677f': '\u5e73\u677f', '\u8033\u673a': '\u8033\u673a', '\u624b\u8868': '\u624b\u8868'} 
    for keyword, label in category_map.items(): 
        if keyword in query: 
            facts['category'] = label 
            break 
    if '\u81ea\u6709\u54c1\u724c' in query: 
        facts['brand_preference'] = '\u81ea\u6709\u54c1\u724c\u4f18\u5148' 
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
        parts.append('\u5f53\u524d\u4efb\u52a1\uff1a' + task_type) 
    if facts.get('budget'): 
        parts.append('\u9884\u7b97\uff1a' + _text(facts.get('budget'))) 
    if facts.get('category'): 
        parts.append('\u54c1\u7c7b\uff1a' + _text(facts.get('category'))) 
    if facts.get('brand_preference'): 
        parts.append('\u54c1\u724c\u504f\u597d\uff1a' + _text(facts.get('brand_preference'))) 
    done_actions = state.get('done_actions') or [] 
    if done_actions: 
        parts.append('\u5df2\u6267\u884c\uff1a' + '\u3001'.join(done_actions[-4:])) 
    candidate_items = state.get('filtered_products') or state.get('retrieved_products') or state.get('comparison_candidates') or [] 
    if candidate_items: 
        names = [] 
        for item in candidate_items[:3]: 
            name = _text((item or {}).get('name')) 
            if name: 
                names.append(name) 
        if names: 
            parts.append('\u5f53\u524d\u5019\u9009\uff1a' + '\u3001'.join(names)) 
    summary = '\uff1b'.join(part for part in parts if part) 
    state['reasoning_summary'] = summary 
