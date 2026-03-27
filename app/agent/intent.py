from __future__ import annotations

from app.agent.schemas import IntentResult


def _text(value):
    return str(value or '').strip()


def _extract_ids(parsed_intent, key):
    values = (parsed_intent or {}).get(key) or []
    out = []
    for value in values:
        text = _text(value)
        if text.isdigit():
            out.append(int(text))
    return out


def detect_intent_rule(user_query, parsed_intent=None):
    query = _text(user_query)
    parsed_intent = parsed_intent or {}
    product_ids = _extract_ids(parsed_intent, 'product_ids')
    candidate_ids = _extract_ids(parsed_intent, 'candidate_ids')
    keywords = []
    compare_words = ('对比', '比较', '区别', '差异', 'vs', 'versus')
    price_words = ('多少钱', '价格', '售价', '降价', '便宜')
    detail_words = ('详情', '参数', '配置', '规格', '介绍')
    recommend_words = ('推荐', '适合', '预算', '买什么', '哪个好', '怎么选')
    if len(product_ids) and len(product_ids) != 1:
        return IntentResult(task_type='compare', confidence=0.99, reason='已有多个商品 ID，直接走对比任务', keywords=['对比'], product_ids=product_ids, candidate_ids=candidate_ids)
    for word in compare_words:
        if word in query:
            keywords.append(word)
            return IntentResult(task_type='compare', confidence=0.9, reason='用户明确在问对比问题', keywords=keywords, product_ids=product_ids, candidate_ids=candidate_ids)
    for word in price_words:
        if word in query:
            keywords.append(word)
            return IntentResult(task_type='price', confidence=0.88, reason='用户在问价格相关信息', keywords=keywords, product_ids=product_ids, candidate_ids=candidate_ids)
    for word in detail_words:
        if word in query:
            keywords.append(word)
            return IntentResult(task_type='detail', confidence=0.86, reason='用户在问商品详情或配置', keywords=keywords, product_ids=product_ids, candidate_ids=candidate_ids)
    for word in recommend_words:
        if word in query:
            keywords.append(word)
            return IntentResult(task_type='recommend', confidence=0.84, reason='用户在问推荐或选购问题', keywords=keywords, product_ids=product_ids, candidate_ids=candidate_ids)
    return IntentResult(task_type='clarify', confidence=0.45, reason='规则层无法高置信判断任务类型', keywords=keywords, product_ids=product_ids, candidate_ids=candidate_ids, need_clarification=True, clarification_question='请再说说你更想要推荐、对比、看详情还是问价格。')


def build_intent_prompt(user_query, parsed_intent=None):
    parsed_intent = parsed_intent or {}
    return chr(10).join([
        '你是智能导购 Agent 的意图分类器。你只负责判断用户当前任务类型，不要回答用户问题，不要提供商品建议。',
        '任务类型只能是 recommend / compare / detail / price / clarify 之一。',
        '用户问题：' + _text(user_query),
        '已有解析上下文：' + str(parsed_intent),
        '请严格输出 IntentResult 结构。',
    ])


async def detect_intent_with_llm(llm, user_query, parsed_intent=None):
    structured_llm = llm.with_structured_output(IntentResult)
    prompt = build_intent_prompt(user_query, parsed_intent=parsed_intent)
    result = await structured_llm.ainvoke(prompt)
    if isinstance(result, IntentResult):
        return result
    return IntentResult.model_validate(result)


def resolve_intent(rule_result, llm_result=None):
    if llm_result is None:
        return rule_result
    if rule_result.task_type != 'clarify':
        return rule_result
    llm_result.product_ids = llm_result.product_ids or rule_result.product_ids
    llm_result.candidate_ids = llm_result.candidate_ids or rule_result.candidate_ids
    return llm_result
