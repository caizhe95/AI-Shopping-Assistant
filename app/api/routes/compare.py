from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db_session
from app.api.routes._trace import trace_from_state
from app.api.schemas.chat import CompareRequest, CompareResponse
from app.services.agent_service import AgentService

router = APIRouter()

@router.post("/compare", response_model=CompareResponse)
async def compare_endpoint(payload: CompareRequest, session: AsyncSession = Depends(get_db_session)):
 service = AgentService(session)
 result = await service.run_compare(payload.session_id, payload.user_query, payload.product_ids, user_id=payload.user_id, max_steps=payload.max_steps)
 state = result.get("state") or {}
 return CompareResponse(session_id=result.get("session_id") or payload.session_id, reply=result.get("response") or "", trace=trace_from_state(state), steps=state.get("steps") or [], comparison=state.get("comparison_result") or {})
