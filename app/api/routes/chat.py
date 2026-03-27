from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db_session
from app.api.routes._trace import trace_from_state
from app.api.schemas.chat import ChatRequest, ChatResponse
from app.services.agent_service import AgentService

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest, session: AsyncSession = Depends(get_db_session)):
 service = AgentService(session)
 result = await service.run_chat(payload.session_id, payload.user_query, user_id=payload.user_id, max_steps=payload.max_steps)
 state = result.get("state") or {}
 return ChatResponse(session_id=result.get("session_id") or payload.session_id, reply=result.get("response") or "", trace=trace_from_state(state), steps=state.get("steps") or [], recommendation=state.get("recommendation_result") or {}, comparison=state.get("comparison_result") or {})
