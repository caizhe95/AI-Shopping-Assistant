from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class IntentResult(BaseModel):
    model_config = ConfigDict(extra='ignore')
    task_type: Literal['recommend', 'compare', 'detail', 'price', 'clarify'] = 'clarify'
    confidence: float = 0.0
    reason: str = ''
    keywords: list[str] = Field(default_factory=list)
    product_ids: list[int] = Field(default_factory=list)
    candidate_ids: list[int] = Field(default_factory=list)
    need_clarification: bool = False
    clarification_question: str = ''


class AgentDecision(BaseModel):
    model_config = ConfigDict(extra='ignore')
    thought: str = ''
    action: Literal['search_products', 'filter_products', 'get_product_detail', 'get_price_info', 'find_similar_products', 'recommend_products', 'compare_products', 'explain_recommendation', 'summarize_comparison', 'ask_clarification', 'finish'] = 'finish'
    action_input: dict[str, Any] = Field(default_factory=dict)
    final_response: str = ''
    done_reason: str = ''
