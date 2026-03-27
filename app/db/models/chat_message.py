from datetime import datetime 
from typing import Any 
 
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func 
from sqlalchemy.orm import Mapped, mapped_column, relationship 
 
from app.db.base import Base 
 
 
class ChatMessage(Base): 
    __tablename__ = 'chat_messages' 
 
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True) 
    session_id: Mapped[str] = mapped_column(ForeignKey('chat_sessions.id', ondelete='CASCADE'), nullable=False, index=True) 
    role: Mapped[str] = mapped_column(String(32), nullable=False) 
    content: Mapped[str] = mapped_column(Text, nullable=False) 
    extra: Mapped[dict[str, Any]] = mapped_column('metadata', JSON, nullable=False, default=dict) 
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now()) 
 
    session = relationship('ChatSession', back_populates='messages')
