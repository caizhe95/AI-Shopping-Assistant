from __future__ import annotations

import json

TASK_ACTIONS = {
    'recommend': ['search_products', 'filter_products', 'recommend_products', 'get_product_detail', 'get_price_info', 'find_similar_products', 'explain_recommendation', 'ask_clarification', 'finish'],
    'compare': ['search_products', 'filter_products', 'compare_products', 'summarize_comparison', 'get_product_detail', 'get_price_info', 'ask_clarification', 'finish'],
    'detail': ['search_products', 'get_product_detail', 'get_price_info', 'ask_clarification', 'finish'],
    'price': ['search_products', 'get_price_info', 'get_product_detail', 'ask_clarification', 'finish'],
    'clarify': ['ask_clarification', 'finish'],
}


def _task_style(task_type):
    if task_type == 'compare':
        return '你是中文商品对比 Agent，要基于事实比较差异、优劣和适合人群。'
    if task_type == 'detail':
        return '你是中文商品详情 Agent，要补全商品参数、规格和价格上下文。'
    if task_type == 'price':
        return '你是中文价格 Agent，要优先补充价格和价格走势相关信息。'
    if task_type == 'clarify':
        return '你是中文导购 Agent，当信息不足时要明确提出澄清问题。'
    return '你是中文智能导购 ReAct Agent，要先搜集事实，再给出明确推荐。'


def build_system_prompt(task_type):
    task_type = str(task_type or 'recommend')
    allowed_actions = TASK_ACTIONS.get(task_type, TASK_ACTIONS['recommend'])
    return chr(10).join([
        _task_style(task_type),
        '',
        '工作规范：',
        '你必须先明确当前任务类型，再决定是否调用工具。',
        '每一轮只能做一个最合理的动作，不要同时做多个动作。',
        '优先使用 tool calling，不要编造商品信息、价格或结论。',
        '不允许重复调用相同参数的工具。',
        '只有当前任务的终局条件满足时，才允许 finish。',
        '如果信息不足，先用工具补事实；工具也不足时再 ask_clarification。',
        '可用动作：' + ', '.join(allowed_actions),
        '',
        '终局条件：',
        '推荐任务只有在形成有效推荐结果时才能 finish。',
        '对比任务只有在形成有效对比结果时才能 finish。',
        '详情任务只有在拿到商品详情时才能 finish。',
        '价格任务只有在拿到价格信息时才能 finish。',
        '',
        '如果不调用工具，你只能输出严格 JSON：',
        '{',
        '  "thought": "简短说明当前判断",',
        '  "action": "ask_clarification 或 finish",',
        '  "action_input": {},',
        '  "final_response": "给用户的回答",',
        '  "done_reason": "为什么可以结束"',
        '}',
    ])


def build_decision_prompt(state):
    snapshot = {
        'task_type': state.get('task_type'),
        'user_query': state.get('user_query'),
        'parsed_intent': state.get('parsed_intent'),
        'retrieved_products': state.get('retrieved_products'),
        'filtered_products': state.get('filtered_products'),
        'recommended_products': state.get('recommended_products'),
        'comparison_candidates': state.get('comparison_candidates'),
        'detail_result': state.get('detail_result'),
        'price_context': state.get('price_context'),
        'last_observation': state.get('last_observation'),
    }
    return chr(10).join([
        '请基于当前 state 决定下一步。',
        '如果已经满足终局条件，请输出 finish。',
        '如果信息不足且工具也无法补足，请输出 ask_clarification。',
        '你只能输出 AgentDecision 结构。',
        json.dumps(snapshot, ensure_ascii=False, default=str),
    ])
