from __future__ import annotations 
 
import json 
 
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage 
from langchain_openai import ChatOpenAI 
from langgraph.graph import END, START, StateGraph 
 
from app.agent.context import build_reasoning_summary, merge_confirmed_facts, trim_messages_window, trim_steps_window 
from app.agent.intent import detect_intent_rule, detect_intent_with_llm, resolve_intent 
from app.agent.observation import compress_observation, normalize_observation 
from app.agent.prompts import build_decision_prompt, build_system_prompt 
from app.agent.retry import build_repair_decision, invoke_with_retry, validate_planner_response 
from app.agent.schemas import AgentDecision, IntentResult 
from app.agent.termination import compute_state_delta, has_meaningful_progress, should_stop_for_loop, snapshot_state, update_thought_tracking 
from app.core.config import settings 
from app.tools import build_compare_tool, build_detail_tool, build_explain_recommendation_tool, build_filter_tool, build_price_tool, build_recommend_tool, build_search_tool, build_similar_tool, build_summarize_comparison_tool 
 
def to_langchain_messages(rows): 
    out = [] 
    for row in rows or []: 
        role = str(row.get('role') or 'user') 
        content = str(row.get('content') or '') 
        if role == 'assistant': 
            out.append(AIMessage(content=content)) 
        elif role == 'system': 
            out.append(SystemMessage(content=content)) 
        else: 
            out.append(HumanMessage(content=content)) 
    return out 
 
def _text(value): 
    return str(value or '').strip() 
 
def _json_text(value): 
    if isinstance(value, str): 
        return value 
    try: 
        return json.dumps(value, ensure_ascii=False, default=str) 
    except Exception: 
        return _text(value)
 
def _parse_json_content(content): 
    raw = _text(content) 
    if not raw: 
        return None 
    try: 
        return json.loads(raw) 
    except Exception: 
        return None 
 
def _normalize_tool_args(args): 
    if args is None: 
        return {} 
    if isinstance(args, dict): 
        return args 
    if isinstance(args, str): 
        parsed = _parse_json_content(args) 
        if isinstance(parsed, dict): 
            return parsed 
        return {'input': args} 
    return {} 
 
def _action_key(tool_name, tool_args): 
    payload = json.dumps(_normalize_tool_args(tool_args), ensure_ascii=False, sort_keys=True, default=str) 
    return str(tool_name) + ':' + payload 
 
def _candidate_items(state): 
    return state.get('filtered_products') or state.get('retrieved_products') or state.get('comparison_candidates') or [] 
 
def _candidate_ids(state): 
    ids = [] 
    for item in _candidate_items(state): 
        if isinstance(item, dict) and item.get('id') is not None: 
            ids.append(int(item.get('id'))) 
    parsed = state.get('parsed_intent') or {} 
    for value in parsed.get('candidate_ids') or []: 
        text = _text(value) 
        if text.isdigit(): 
            ids.append(int(text)) 
    return list(dict.fromkeys(ids)) 
 
def _has_recommendation(state): 
    result = state.get('recommendation_result') or {} 
    return bool(state.get('recommended_products') or result.get('recommended_products') or result.get('product_list')) 
 
def _has_comparison(state): 
    result = state.get('comparison_result') or {} 
    return bool(result or state.get('comparison_candidates') or result.get('products') or result.get('product_list')) 
 
def _has_detail(state): 
    return bool(state.get('detail_result')) 
 
def _has_price(state): 
    return bool(state.get('price_context'))
 
def _is_task_finished(state): 
    task_type = _text(state.get('task_type') or state.get('mode') or 'recommend') 
    if task_type == 'compare': 
        return _has_comparison(state) 
    if task_type == 'detail': 
        return _has_detail(state) 
    if task_type == 'price': 
        return _has_price(state) 
    if task_type == 'clarify': 
        return bool(state.get('clarification_question') or state.get('final_response')) 
    return _has_recommendation(state) 
 
def _build_best_effort_response(state): 
    if _has_recommendation(state): 
        return '已达到最大步数，返回当前最佳推荐结果' 
    if _has_comparison(state): 
        return '已达到最大步数，返回当前最佳对比结果' 
    if _has_detail(state): 
        return '已达到最大步数，返回当前最佳详情结果' 
    if _has_price(state): 
        return '已达到最大步数，返回当前最佳价格结果' 
    if _candidate_items(state): 
        return '已达到最大步数，返回当前候选结果，请补充更明确的需求' 
    return '已达到最大步数，当前信息仍不足，请补充更明确的需求' 
 
def _remember_action(state, tool_name, tool_args): 
    key = _action_key(tool_name, tool_args) 
    state['done_action_keys'] = list(dict.fromkeys((state.get('done_action_keys') or []) + [key])) 
    state['done_actions'] = list(dict.fromkeys((state.get('done_actions') or []) + [tool_name])) 
    usage = dict(state.get('tool_usage_stats') or {}) 
    usage[tool_name] = int(usage.get(tool_name) or 0) +  1
    state['tool_usage_stats'] = usage 
 
def _should_skip_action(state, tool_name, tool_args): 
    key = _action_key(tool_name, tool_args) 
    return key in (state.get('done_action_keys') or []) 
 
def _tool_action_allowed(state, tool_name, tool_args): 
    task_type = _text(state.get('task_type') or 'recommend') 
    product_ids = (state.get('parsed_intent') or {}).get('product_ids') or [] 
    compare_ids = tool_args.get('product_ids') if isinstance(tool_args, dict) else [] 
    if task_type == 'recommend': 
        return tool_name in ('search_products', 'filter_products', 'recommend_products', 'explain_recommendation') 
    if task_type == 'compare': 
        if tool_name == 'compare_products': 
            ids = compare_ids or product_ids or _candidate_ids(state) 
            return len(ids) not in (0, 1) 
        return tool_name in ('search_products', 'filter_products', 'find_similar_products', 'get_product_detail', 'summarize_comparison') 
    if task_type == 'detail': 
        return tool_name in ('search_products', 'filter_products', 'get_product_detail', 'get_price_info', 'find_similar_products') 
    if task_type == 'price': 
        return tool_name in ('search_products', 'filter_products', 'get_price_info', 'get_product_detail') 
    return tool_name in ('search_products', 'filter_products')
 
def _clarification_question_for_task(state): 
    task_type = _text(state.get('task_type') or 'recommend') 
    if task_type == 'compare': 
        return '请告诉我要对比的两款商品，或直接提供商品编号。' 
    if task_type == 'detail': 
        return '请告诉我你想看的具体商品，或直接提供商品编号。' 
    if task_type == 'price': 
        return '请告诉我你想查询价格的具体商品，或直接提供商品编号。' 
    return '请补充你想买的品类、预算、品牌偏好或使用场景，我再继续推荐。' 
 
def _merge_tool_result(state, tool_name, result): 
    if not isinstance(result, dict): 
        return 
    data = result.get('data') or {} 
    if isinstance(data, dict): 
        state.update(data) 
    if tool_name in ('search_products', 'filter_products'): 
        items = data.get('filtered_products') or data.get('retrieved_products') or data.get('product_list') or [] 
        state['retrieved_products'] = data.get('retrieved_products') or items or state.get('retrieved_products') or [] 
        state['filtered_products'] = data.get('filtered_products') or items or state.get('filtered_products') or [] 
    elif tool_name == 'recommend_products': 
        new_items = data.get('recommended_products') or data.get('product_list') or [] 
        if new_items: 
            state['recommendation_result'] = data 
            state['recommended_products'] = new_items 
    elif tool_name == 'compare_products': 
        state['comparison_result'] = data 
        state['comparison_candidates'] = data.get('products') or data.get('product_list') or data.get('comparison_candidates') or [] 
    elif tool_name == 'get_product_detail': 
        state['detail_result'] = data.get('detail_result') or data.get('product_detail') or {} 
        state['price_context'] = data.get('price_context') or state.get('price_context') or {} 
    elif tool_name == 'get_price_info': 
        state['price_context'] = data.get('price_context') or data.get('price_result') or {} 
    elif tool_name == 'find_similar_products': 
        state['comparison_candidates'] = data.get('comparison_candidates') or data.get('similar_products') or [] 
 
def _build_tools(session): 
    tools = [build_search_tool(session), build_filter_tool(session), build_detail_tool(session), build_price_tool(session), build_similar_tool(session), build_recommend_tool(session), build_compare_tool(session), build_explain_recommendation_tool(session), build_summarize_comparison_tool(session)] 
    return tools, {tool.name: tool for tool in tools} 
 
def _build_llm(): 
    api_key = settings.effective_llm_api_key 
    if not api_key: 
        raise RuntimeError('LLM API key is not configured') 
    return ChatOpenAI(model=settings.effective_llm_model, base_url=settings.effective_llm_base_url, api_key=api_key, temperature=0)
 
class _AgentRuntime: 
    def __init__(self, session, mode='chat'): 
        self.session = session 
        self.mode = mode 
        self.llm = _build_llm() 
        self.tools, self.tool_map = _build_tools(session) 
        self.bound_llm = self.llm.bind_tools(self.tools) 
        self.decision_llm = self.llm.with_structured_output(AgentDecision) 
 
    async def _run_tool(self, name, args): 
        tool = self.tool_map.get(name) 
        if tool is None: 
            return {'summary': '未知工具', 'data': {'error': 'Unknown tool: ' + str(name)}} 
        return await tool.ainvoke(args) 
 
    async def detect_intent_node(self, state): 
        state = dict(state or {}) 
        parsed_intent = state.get('parsed_intent') or {} 
        mode = _text(state.get('mode') or self.mode or 'chat') 
        if mode == 'recommend': 
            intent = IntentResult(task_type='recommend', confidence=1.0, reason='接口已指定为推荐任务', candidate_ids=parsed_intent.get('candidate_ids') or []) 
        elif mode == 'compare': 
            intent = IntentResult(task_type='compare', confidence=1.0, reason='接口已指定为对比任务', product_ids=parsed_intent.get('product_ids') or []) 
        else: 
            rule_result = detect_intent_rule(state.get('user_query'), parsed_intent=parsed_intent) 
            llm_result = None 
            if rule_result.task_type == 'clarify': 
                try: 
                    llm_result = await detect_intent_with_llm(self.llm, state.get('user_query'), parsed_intent=parsed_intent) 
                except Exception: 
                    llm_result = None 
            intent = resolve_intent(rule_result, llm_result) 
        state['task_type'] = intent.task_type 
        state['task_reason'] = intent.reason 
        state['task_confidence'] = intent.confidence 
        state['parsed_intent'] = {'product_ids': intent.product_ids, 'candidate_ids': intent.candidate_ids, 'keywords': intent.keywords} 
        state['needs_clarification'] = bool(intent.need_clarification) 
        if intent.clarification_question: 
            state['clarification_question'] = intent.clarification_question 
        merge_confirmed_facts(state) 
        build_reasoning_summary(state) 
        return state 
 
    def _fallback_action(self, state): 
        task_type = _text(state.get('task_type') or 'recommend') 
        query = _text(state.get('user_query')) 
        ids = _candidate_ids(state) 
        product_ids = (state.get('parsed_intent') or {}).get('product_ids') or [] 
        done_actions = state.get('done_actions') or [] 
        if task_type == 'compare': 
            compare_ids = product_ids or ids 
            if len(compare_ids) not in (0, 1): 
                return 'compare_products', {'product_ids': compare_ids[:4]} 
            if 'search_products' not in done_actions: 
                return 'search_products', {'query': query, 'limit': 6} 
            return 'ask_clarification', {'question': '请告诉我要对比的两款商品，或直接提供商品编号。'} 
        if task_type == 'detail': 
            target_id = (product_ids or ids or [None])[0] 
            if target_id and 'get_product_detail' not in done_actions: 
                return 'get_product_detail', {'product_id': target_id} 
            if 'search_products' not in done_actions: 
                return 'search_products', {'query': query, 'limit': 6} 
            return 'ask_clarification', {'question': '请告诉我你想看的具体商品，或直接提供商品编号。'} 
        if task_type == 'price': 
            target_id = (product_ids or ids or [None])[0] 
            if target_id and 'get_price_info' not in done_actions: 
                return 'get_price_info', {'product_id': target_id} 
            if 'search_products' not in done_actions: 
                return 'search_products', {'query': query, 'limit': 6} 
            return 'ask_clarification', {'question': '请告诉我你想查询价格的具体商品，或直接提供商品编号。'} 
        if 'search_products' not in done_actions: 
            return 'search_products', {'query': query, 'limit': 6} 
        if ids and 'filter_products' not in done_actions: 
            return 'filter_products', {'query': query, 'candidate_ids': ids[:8], 'limit': 6} 
        if ids: 
            return 'recommend_products', {'query': query, 'candidate_ids': ids[:6], 'limit': 5} 
        return 'ask_clarification', {'question': '请补充你想买的品类、预算或使用场景，我再继续推荐。'}
 
    async def plan_node(self, state): 
        state = dict(state or {}) 
        merge_confirmed_facts(state) 
        build_reasoning_summary(state) 
        if _is_task_finished(state): 
            state['done'] = True 
            state['done_reason'] = state.get('done_reason') or '已满足当前任务终局条件' 
            return state 
        max_steps = int(state.get('max_steps') or 6) 
        if max_steps and len(state.get('steps') or []) == max_steps: 
            state['done'] = True 
            state['done_reason'] = '已达到最大步数，返回当前最佳结果' 
            state['final_response'] = state.get('final_response') or _build_best_effort_response(state) 
            return state 
        if should_stop_for_loop(state): 
            state['done'] = True 
            state['done_reason'] = state.get('done_reason') or '检测到重复思考或连续无进展，已提前终止' 
            state['final_response'] = state.get('final_response') or _build_best_effort_response(state) 
            return state 
        messages = list(state.get('messages') or []) 
        system_prompt = build_system_prompt(state.get('task_type')) 
        if not messages or not isinstance(messages[0], SystemMessage): 
            messages = [SystemMessage(content=system_prompt)] + messages 
        else: 
            messages[0] = SystemMessage(content=system_prompt) 
        working_messages = trim_messages_window(messages, max_messages=8) 
        assistant = await invoke_with_retry(self.bound_llm, working_messages, validator=validate_planner_response) 
        if not isinstance(assistant, AIMessage): 
            assistant = AIMessage(content=_text(assistant)) 
        messages = list(working_messages) + [assistant] 
        state['messages'] = messages 
        content = _text(assistant.content) 
        if content: 
            state['thought'] = content 
            update_thought_tracking(state, content) 
        if should_stop_for_loop(state): 
            state['done'] = True 
            state['done_reason'] = state.get('done_reason') or '检测到重复思考或连续无进展，已提前终止' 
            state['final_response'] = state.get('final_response') or _build_best_effort_response(state) 
            return state 
        tool_calls = list(getattr(assistant, 'tool_calls', None) or []) 
        if tool_calls: 
            call = tool_calls[0] or {} 
            action = _text(call.get('name')) 
            action_input = _normalize_tool_args(call.get('args')) 
            if _tool_action_allowed(state, action, action_input): 
                state['pending_action'] = action 
                state['pending_action_input'] = action_input 
                state['pending_tool_call_id'] = _text(call.get('id')) or action 
                return state 
        decision_state = dict(state) 
        decision_state['steps'] = trim_steps_window(state.get('steps') or [], max_steps=4) 
        try: 
            decision = await self.decision_llm.ainvoke(build_decision_prompt(decision_state)) 
            if not isinstance(decision, AgentDecision): 
                decision = AgentDecision.model_validate(decision) 
        except Exception: 
            parsed = _parse_json_content(content) or {} 
            if parsed: 
                decision = AgentDecision.model_validate(parsed) 
            else: 
                decision = build_repair_decision(content) 
        state['thought'] = _text(decision.thought) or state.get('thought') or '' 
        if decision.done_reason: 
            state['done_reason'] = decision.done_reason 
        if decision.action == 'ask_clarification': 
            question = _text((decision.action_input or {}).get('question') or state.get('clarification_question') or decision.final_response) 
            state['clarification_question'] = question or state.get('clarification_question') or '请补充品类、预算或想要对比的商品。' 
            state['final_response'] = state['clarification_question'] 
            state['done'] = True 
            return state 
        if decision.action == 'finish' and _is_task_finished(state): 
            state['final_response'] = _text(decision.final_response) or state.get('final_response') or _build_best_effort_response(state) 
            state['done'] = True 
            return state 
        if decision.action != 'finish' and _tool_action_allowed(state, decision.action, _normalize_tool_args(decision.action_input)): 
            state['pending_action'] = decision.action 
            state['pending_action_input'] = _normalize_tool_args(decision.action_input) 
            state['pending_tool_call_id'] = decision.action 
            return state 
        action, action_input = self._fallback_action(state) 
        if action == 'ask_clarification': 
            question = _text((action_input or {}).get('question')) or '请补充你的需求。' 
            state['clarification_question'] = question 
            state['final_response'] = question 
            state['done_reason'] = state.get('done_reason') or '当前信息不足，已转为澄清问题' 
            state['done'] = True 
            return state 
        state['pending_action'] = action 
        state['pending_action_input'] = action_input 
        state['pending_tool_call_id'] = action 
        return state
 
    async def act_node(self, state): 
        state = dict(state or {}) 
        tool_name = _text(state.get('pending_action')) 
        tool_args = _normalize_tool_args(state.get('pending_action_input')) 
        if not tool_name: 
            state['done'] = True 
            return state 
        if _should_skip_action(state, tool_name, tool_args): 
            state['done'] = True 
            state['done_reason'] = state.get('done_reason') or '检测到重复动作，为防止循环已停止' 
            state['final_response'] = state.get('final_response') or _build_best_effort_response(state) 
            return state 
        before_snapshot = snapshot_state(state) 
        raw_observation = await self._run_tool(tool_name, tool_args) 
        observation = normalize_observation(tool_name, raw_observation) 
        _remember_action(state, tool_name, tool_args) 
        _merge_tool_result(state, tool_name, observation) 
        merge_confirmed_facts(state) 
        build_reasoning_summary(state) 
        after_snapshot = snapshot_state(state) 
        delta = compute_state_delta(before_snapshot, after_snapshot) 
        state['state_delta'] = delta 
        if has_meaningful_progress(delta):
            state['no_progress_count'] = 0
        else:
            state['no_progress_count'] = int(state.get('no_progress_count') or 0) + 1
        summary = compress_observation(tool_name, observation)
        messages = list(state.get('messages') or []) 
        messages.append(ToolMessage(content=_json_text(observation), tool_call_id=_text(state.get('pending_tool_call_id')) or tool_name)) 
        state['messages'] = messages 
        step = {'index': len(state.get('steps') or []) + 1, 'task_type': state.get('task_type') or '', 'thought': state.get('thought') or tool_name, 'action': tool_name, 'action_input': tool_args, 'observation': observation, 'observation_summary': summary, 'final_response': '', 'done_reason': '', 'state_delta': delta, 'error': '', 'is_final': False} 
        state['steps'] = list(state.get('steps') or []) + [step] 
        state['step_count'] = len(state['steps']) 
        state['last_observation'] = observation 
        state['tool_result'] = observation if isinstance(observation, dict) else {'value': observation} 
        state['pending_action'] = '' 
        state['pending_action_input'] = {} 
        if isinstance(observation, dict) and observation.get('should_continue') is False and not observation.get('enough_for_finish'): 
            next_actions = observation.get('next_best_actions') or [] 
            if 'ask_clarification' in next_actions: 
                question = _clarification_question_for_task(state) 
                state['needs_clarification'] = True 
                state['clarification_question'] = question 
                state['final_response'] = question 
                state['done_reason'] = state.get('done_reason') or '工具观察表明信息不足，已转为澄清问题' 
                state['done'] = True 
                state['steps'][-1]['is_final'] = True 
                state['steps'][-1]['done_reason'] = state['done_reason'] 
                state['steps'][-1]['final_response'] = question 
                return state 
        max_steps = int(state.get('max_steps') or 6) 
        if max_steps and len(state.get('steps') or []) == max_steps: 
            state['done'] = True 
            state['done_reason'] = '已达到最大步数，返回当前最佳结果' 
            state['final_response'] = state.get('final_response') or _build_best_effort_response(state) 
            state['steps'][-1]['is_final'] = True 
            state['steps'][-1]['done_reason'] = state['done_reason'] 
            state['steps'][-1]['final_response'] = state['final_response'] 
            return state 
        if should_stop_for_loop(state): 
            state['done'] = True 
            state['done_reason'] = state.get('done_reason') or '检测到重复思考或连续无进展，已提前终止' 
            state['final_response'] = state.get('final_response') or _build_best_effort_response(state) 
            state['steps'][-1]['is_final'] = True 
            state['steps'][-1]['done_reason'] = state['done_reason'] 
            state['steps'][-1]['final_response'] = state['final_response'] 
            return state 
        if _is_task_finished(state): 
            state['done'] = True 
            state['done_reason'] = state.get('done_reason') or '工具观察已满足任务终局条件' 
            state['steps'][-1]['is_final'] = True 
            state['steps'][-1]['done_reason'] = state['done_reason'] 
        return state 
 
def _route_after_detect(state): 
    return 'plan' 
 
def _route_after_plan(state): 
    if state.get('done'): 
        return END 
    if _text(state.get('pending_action')): 
        return 'act' 
    return END 
 
def _route_after_act(state): 
    if state.get('done'): 
        return END 
    return 'plan' 
 
def build_agent_graph(session, mode='chat'): 
    runtime = _AgentRuntime(session, mode=mode) 
    builder = StateGraph(dict) 
    builder.add_node('detect_intent', runtime.detect_intent_node) 
    builder.add_node('plan', runtime.plan_node) 
    builder.add_node('act', runtime.act_node) 
    builder.add_edge(START, 'detect_intent') 
    builder.add_conditional_edges('detect_intent', _route_after_detect) 
    builder.add_conditional_edges('plan', _route_after_plan) 
    builder.add_conditional_edges('act', _route_after_act) 
    return builder.compile()
