from app.api.schemas.common import Trace 
 
def _append_unique(items, value): 
 if not value: 
  return 
 if not items or items[-1] != value: 
  items.append(value) 
 
def trace_from_state(state): 
 state = state or {} 
 steps = state.get('steps') or [] 
 thought = '' 
 action_path = [] 
 observation_summaries = [] 
 for step in steps: 
  if not isinstance(step, dict): 
   continue 
  step_thought = str(step.get('thought') or '') 
  if step_thought: 
   thought = step_thought 
  action = str(step.get('action') or '') 
  _append_unique(action_path, action) 
  summary = str(step.get('observation_summary') or '') 
  _append_unique(observation_summaries, summary[:200]) 
 if not thought: 
  thought = str(state.get('thought') or state.get('final_response') or '') 
 stats = dict(state.get('tool_usage_stats') or {}) 
 return Trace(thought=thought, action_path=action_path, observation_summaries=observation_summaries, stats=stats) 
