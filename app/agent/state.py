from __future__ import annotations 
from typing import Any, Literal, TypedDict 
 
ActionName = Literal['ask_clarification', 'search_products', 'filter_products', 'get_product_detail', 'get_price_info', 'find_similar_products', 'recommend_products', 'compare_products', 'explain_recommendation', 'summarize_comparison', 'finish'] 
 
 
class AgentStep(TypedDict, total=False): 
    index: int 
    task_type: str 
    thought: str 
    action: ActionName 
    action_input: dict[str, Any] 
    observation: Any 
    observation_summary: str 
    final_response: str 
    done_reason: str 
    state_delta: dict[str, Any] 
    error: str 
    is_final: bool 
 
 
class AgentState(TypedDict, total=False): 
    session_id: str 
    user_id: str 
    mode: str 
    user_query: str 
    task_context: str 
    task_type: str 
    task_reason: str 
    task_confidence: float 
    parsed_intent: dict[str, Any] 
    missing_slots: list[str] 
    messages: list[Any] 
    steps: list[AgentStep] 
    step_count: int 
    max_steps: int 
    reasoning_summary: str 
    conversation_summary: str 
    confirmed_facts: dict[str, Any] 
    thought_history: list[str] 
    repeat_thought_count: int 
    no_progress_count: int 
    retrieved_products: list[dict[str, Any]] 
    filtered_products: list[dict[str, Any]] 
    selected_product_ids: list[int] 
    recommended_products: list[dict[str, Any]] 
    comparison_candidates: list[dict[str, Any]] 
    price_context: dict[str, Any] 
    detail_result: dict[str, Any] 
    clarification_question: str 
    needs_clarification: bool 
    recommendation_result: dict[str, Any] 
    comparison_result: dict[str, Any] 
    tool_result: dict[str, Any] 
    thought: str 
    pending_action: ActionName 
    pending_action_input: dict[str, Any] 
    last_observation: Any 
    done_actions: list[str] 
    done_action_keys: list[str] 
    done_reason: str 
    final_response: str 
    done: bool 
    error: str
