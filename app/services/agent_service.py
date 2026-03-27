from __future__ import annotations

import json
import uuid
from datetime import datetime

from langchain_core.messages import HumanMessage

from app.agent.context import build_reasoning_summary, merge_confirmed_facts
from app.agent.graph import build_agent_graph, to_langchain_messages
from app.db.repositories.chat_repository import ChatRepository
from app.services.response_composer import compose_response

def _normalize_text(value):
 return str(value or "").strip()


def _clean_trace_text(value):
 text = _normalize_text(value)
 if not text:
  return ""
 if text.startswith("{") or text.startswith("```"):
  try:
   parsed = json.loads(text.strip("`").replace("json\n", "", 1).replace("JSON\n", "", 1).strip())
   if isinstance(parsed, dict):
    candidate = _normalize_text(parsed.get("thought") or parsed.get("final_response") or parsed.get("reply"))
    if candidate:
     return candidate
  except Exception:
   return ""
 if "\n" in text:
  text = text.splitlines()[0]
 return text[:120]

def _sanitize_trace_state(state):
 if not isinstance(state, dict):
  return state
 state["thought"] = _clean_trace_text(state.get("thought") or state.get("final_response") or state.get("reply"))
 steps = state.get("steps") or []
 for step in steps:
  if isinstance(step, dict) and step.get("thought"):
   step["thought"] = _clean_trace_text(step.get("thought")) or step.get("thought")
 return state

class AgentService:
 def __init__(self, session):
  self.session = session
  self.chat_repo = ChatRepository(session)

 def _ensure_session_id(self, session_id):
  value = _normalize_text(session_id)
  return value or uuid.uuid4().hex

 async def _persist(self, session_id, user_query, response, user_id, mode):
  await self.chat_repo.get_or_create_session(session_id, user_id=user_id)
  if user_query:
   await self.chat_repo.append_message(session_id, "user", user_query)
  if response:
   await self.chat_repo.append_message(session_id, "assistant", response, extra={"mode": mode})
  await self.chat_repo.update_session_activity(session_id, last_message_at=datetime.utcnow())
  await self.session.commit()

 async def _run_graph(self, mode, session_id, user_query, user_id=None, task_context=None, parsed_intent=None, max_steps=None):
  sid = self._ensure_session_id(session_id)
  query = _normalize_text(user_query)
  await self.chat_repo.get_or_create_session(sid, user_id=user_id)
  history = await self.chat_repo.list_messages(sid, limit=12)
  messages = to_langchain_messages([{"role": row.role, "content": row.content} for row in history])
  if query:
   messages.append(HumanMessage(content=query))
  graph = build_agent_graph(self.session, mode=mode)
  state = {
   "session_id": sid,
   "user_id": user_id,
   "mode": mode,
   "user_query": query,
   "task_context": task_context or "",
   "task_type": "",
   "task_reason": "",
   "task_confidence": 0.0,
   "parsed_intent": parsed_intent or {},
   "missing_slots": [],
   "messages": messages,
   "steps": [],
   "step_count": 0,
   "max_steps": int(max_steps or 6),
   "reasoning_summary": "",
   "conversation_summary": "",
   "confirmed_facts": {},
   "thought_history": [],
   "repeat_thought_count": 0,
   "no_progress_count": 0,
   "recommendation_result": {},
   "comparison_result": {},
   "pending_action_input": {},
   "last_observation": {},
   "needs_clarification": False,
   "done_reason": "",
   "done_actions": [],
   "done_action_keys": [],
   "final_response": "",
   "done": False,
   "error": "",
  }
  merge_confirmed_facts(state)
  build_reasoning_summary(state)
  result_state = await graph.ainvoke(state, config={"recursion_limit": max(8, int(max_steps or 6) * 3)})
  result_state = _sanitize_trace_state(result_state)
  response = compose_response(mode, result_state)
  result_state["final_response"] = response
  await self._persist(sid, query, response, user_id, mode)
  return {"session_id": sid, "response": response, "state": result_state}

 async def run_chat(self, session_id, user_query, user_id=None, max_steps=None):
  return await self._run_graph("chat", session_id, user_query, user_id=user_id, max_steps=max_steps)

 async def run_compare(self, session_id, user_query, product_ids=None, user_id=None, max_steps=None):
  ids = [int(pid) for pid in (product_ids or [])]
  context = "对比商品ID: " + ", ".join(str(pid) for pid in ids) + "。" if ids else ""
  intent = {"product_ids": ids}
  query = user_query or "请对比这些商品。"
  return await self._run_graph("compare", session_id, query, user_id=user_id, task_context=context, parsed_intent=intent, max_steps=max_steps)

 async def run_recommend(self, session_id, user_query, candidate_ids=None, user_id=None, max_steps=None):
  ids = [int(pid) for pid in (candidate_ids or [])]
  intent = {"candidate_ids": ids}
  query = user_query or "请推荐合适的商品。"
  return await self._run_graph("recommend", session_id, query, user_id=user_id, parsed_intent=intent, max_steps=max_steps)
