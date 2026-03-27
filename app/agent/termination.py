from __future__ import annotations 
 
def _text(value): 
    return str(value or '').strip() 
 
def snapshot_state(state): 
    def _ids(items): 
        out = [] 
        for item in items or []: 
            if isinstance(item, dict) and item.get('id') is not None: 
                out.append(int(item.get('id'))) 
        return out 
    return { 
        'retrieved_ids': _ids(state.get('retrieved_products') or []), 
        'filtered_ids': _ids(state.get('filtered_products') or []), 
        'recommended_ids': _ids(state.get('recommended_products') or []), 
        'has_comparison': bool(state.get('comparison_result')), 
        'has_detail': bool(state.get('detail_result')), 
        'has_price': bool(state.get('price_context')), 
        'facts': dict(state.get('confirmed_facts') or {}), 
    } 
 
def compute_state_delta(before, after): 
    delta = {} 
    for key in ('retrieved_ids', 'filtered_ids', 'recommended_ids'): 
        before_ids = set(before.get(key) or []) 
        after_ids = set(after.get(key) or []) 
        new_ids = list(after_ids - before_ids) 
        if new_ids: 
            delta[key] = sorted(new_ids) 
    for key in ('has_comparison', 'has_detail', 'has_price'): 
        if not before.get(key) and after.get(key): 
            delta[key] = True 
    before_facts = before.get('facts') or {} 
    after_facts = after.get('facts') or {} 
    new_fact_keys = [key for key in after_facts if before_facts.get(key) != after_facts.get(key)] 
    if new_fact_keys: 
        delta['facts'] = {key: after_facts.get(key) for key in new_fact_keys} 
    return delta 
 
def has_meaningful_progress(delta): 
    return bool(delta) 
 
def normalize_thought(text): 
    normalized = ''.join(_text(text).split()) 
    return normalized[:80] 
 
def update_thought_tracking(state, thought): 
    history = list(state.get('thought_history') or []) 
    normalized = normalize_thought(thought) 
    if not normalized: 
        state['thought_history'] = history[-4:] 
        return 
    repeated = bool(history and history[-1] == normalized) 
    history.append(normalized) 
    state['thought_history'] = history[-4:] 
    state['repeat_thought_count'] = int(state.get('repeat_thought_count') or 0) + 1 if repeated else 0 
 
def should_stop_for_loop(state): 
    repeat_count = int(state.get('repeat_thought_count') or 0) 
    no_progress_count = int(state.get('no_progress_count') or 0) 
    if repeat_count not in (0, 1): 
        return True 
    if no_progress_count not in (0, 1): 
        return True 
    return False
