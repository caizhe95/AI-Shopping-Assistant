from typing import Any 
 
from pydantic import BaseModel, ConfigDict, Field 
 
 
class Trace(BaseModel): 
    model_config = ConfigDict(extra='ignore') 
    thought: str = '' 
    action_path: list[str] = Field(default_factory=list) 
    observation_summaries: list[str] = Field(default_factory=list) 
    stats: dict[str, int] = Field(default_factory=dict) 
 
 
class TraceStep(BaseModel): 
    model_config = ConfigDict(extra='ignore') 
    index: int = 0
    task_type: str = '' 
    thought: str = '' 
    action: str = '' 
    action_input: dict[str, Any] = Field(default_factory=dict) 
    observation: Any = None 
    observation_summary: str = '' 
    final_response: str = '' 
    done_reason: str = '' 
    state_delta: dict[str, Any] = Field(default_factory=dict) 
    error: str = '' 
    is_final: bool = False 
 
 
class APIMessage(BaseModel): 
    detail: str 
