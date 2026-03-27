from datetime import datetime 
from sqlalchemy import desc, select 
from sqlalchemy.ext.asyncio import AsyncSession 
from app.db.models.chat_message import ChatMessage 
from app.db.models.chat_session import ChatSession 
class ChatRepository: 
    def __init__(self, session: AsyncSession): self.session = session 
    async def get_or_create_session(self, session_id: str, user_id: str = None): 
        obj = await self.session.get(ChatSession, session_id) 
        if obj: return obj 
        obj = ChatSession(id=session_id, user_id=user_id); self.session.add(obj); await self.session.flush(); return obj 
    async def append_message(self, session_id: str, role: str, content: str, extra: dict = None): 
        obj = ChatMessage(session_id=session_id, role=role, content=content, extra=extra or {}); self.session.add(obj); await self.session.flush(); return obj 
    async def list_messages(self, session_id: str, limit: int = 20): 
        stmt = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(desc(ChatMessage.id)).limit(limit); rows = await self.session.scalars(stmt); return list(reversed(rows.all())) 
    async def update_session_activity(self, session_id: str, last_message_at: datetime = None): 
        obj = await self.session.get(ChatSession, session_id) 
        if obj: obj.last_message_at = last_message_at or datetime.utcnow() 
    async def update_summary(self, session_id: str, summary: str): 
        obj = await self.session.get(ChatSession, session_id) 
