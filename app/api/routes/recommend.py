from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db_session
from app.api.routes._trace import trace_from_state
from app.api.schemas.chat import RecommendRequest, RecommendResponse
from app.services.agent_service import AgentService

router = APIRouter()

@router.post("/recommend", response_model=RecommendResponse)
async def recommend_endpoint(payload: RecommendRequest, session: AsyncSession = Depends(get_db_session)):
 service = AgentService(session)
 result = await service.run_recommend(payload.session_id, payload.user_query, payload.candidate_ids, user_id=payload.user_id, max_steps=payload.max_steps)
 state = result.get("state") or {}
 return RecommendResponse(session_id=result.get("session_id") or payload.session_id, reply=result.get("response") or "", trace=trace_from_state(state), steps=state.get("steps") or [], recommendation=state.get("recommendation_result") or {})
