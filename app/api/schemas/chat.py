from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.api.schemas.common import Trace, TraceStep

class ChatRequest(BaseModel):
 model_config = ConfigDict(extra="ignore")
 session_id: str
 user_query: str
 user_id: Optional[str] = None
 max_steps: Optional[int] = None

class CompareRequest(BaseModel):
 model_config = ConfigDict(extra="ignore")
 session_id: str
 user_query: str = ""
 product_ids: list[int] = Field(default_factory=list)
 user_id: Optional[str] = None
 max_steps: Optional[int] = None

class RecommendRequest(BaseModel):
 model_config = ConfigDict(extra="ignore")
 session_id: str
 user_query: str = ""
 candidate_ids: list[int] = Field(default_factory=list)
 user_id: Optional[str] = None
 max_steps: Optional[int] = None

class ChatResponse(BaseModel):
 session_id: str
 reply: str
 trace: Trace = Field(default_factory=Trace)
 steps: list[TraceStep] = Field(default_factory=list)
 recommendation: dict = Field(default_factory=dict)
 comparison: dict = Field(default_factory=dict)

class CompareResponse(ChatResponse):
 pass

class RecommendResponse(ChatResponse):
 pass

BargainRequest = RecommendRequest
