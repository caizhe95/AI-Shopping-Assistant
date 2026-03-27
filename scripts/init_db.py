from __future__ import annotations  
  
import asyncio  
import sys  
from pathlib import Path  
  
from sqlalchemy.ext.asyncio import create_async_engine  
  
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  
  
from app.core.config import settings  
from app.db.base import Base  
from app.db.models import ChatMessage, ChatSession, Product, ProductPriceSnapshot  # noqa: F401  
  
async def init_db():  
    engine = create_async_engine(settings.database_url, echo=settings.debug, pool_pre_ping=True)  
    async with engine.begin() as conn:  
        await conn.run_sync(Base.metadata.create_all)  
    await engine.dispose()  
  
if __name__ == '__main__':  
    asyncio.run(init_db()) 
