from __future__ import annotations 
 
from app.agent.schemas import AgentDecision 
 
def _has_tool_call(response): 
    return bool(getattr(response, 'tool_calls', None) or []) 
 
async def invoke_with_retry(bound_llm, messages, validator=None): 
    response = await bound_llm.ainvoke(messages) 
    if validator is None or validator(response): 
        return response 
    repair_messages = list(messages) + [('system', '上一轮输出不合规。请严格遵守工具调用规则；如果不调用工具，就输出合法的 AgentDecision JSON。')] 
    return await bound_llm.ainvoke(repair_messages) 
 
def validate_planner_response(response): 
    if _has_tool_call(response): 
        return True 
    content = str(getattr(response, 'content', '') or '').strip() 
    return content.startswith('{') and content.endswith('}') 
 
def build_repair_decision(raw_text): 
    text = str(raw_text or '').strip() 
    return AgentDecision(thought=text[:80], action='ask_clarification', action_input={'question': '请补充更明确的需求。'}, final_response='请补充更明确的需求。', done_reason='模型输出不合规，已降级为澄清问题')
