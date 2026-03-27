from __future__ import annotations 
 
import json 
import logging 
 
from app.db.repositories.chat_repository import ChatRepository 
from app.infra.redis_client import get_redis 
 
logger = logging.getLogger(__name__) 
 
 
class MemoryService: 
    def __init__(self, session, redis=None): 
        self.chat_repo = ChatRepository(session) 
        self.redis = redis 
 
    async def _redis(self): 
        try: 
            return self.redis or await get_redis() 
        except Exception as exc: 
            logger.warning('Redis unavailable, fallback to empty cache: %s', exc) 
            return None 
 
    async def _safe_get_json(self, key): 
        redis = await self._redis() 
        if redis is None: 
            return None 
        try: 
            raw = await redis.get(key) 
            return json.loads(raw) if raw else None 
        except Exception as exc: 
            logger.warning('Redis read failed, cache skipped: %s', exc) 
            return None 
 
    async def _safe_set_json(self, key, payload, ttl): 
        redis = await self._redis() 
        if redis is None: 
            return 
        try: 
            await redis.set(key, json.dumps(payload, ensure_ascii=False), ex=ttl) 
        except Exception as exc: 
            logger.warning('Redis write failed, cache skipped: %s', exc) 
 
    async def get_session_context(self, session_id): 
        return await self._safe_get_json(f'session:{session_id}') 
 
    async def set_session_context(self, session_id, payload, ttl=3600): 
        await self._safe_set_json(f'session:{session_id}', payload, ttl) 
 
    async def cache_product_detail(self, product_id, payload, ttl=1800): 
        await self._safe_set_json(f'product:{product_id}', payload, ttl) 
 
    async def get_cached_product_detail(self, product_id): 
        return await self._safe_get_json(f'product:{product_id}') 
 
    async def cache_compare_result(self, key, payload, ttl=1800): 
        await self._safe_set_json(f'compare:{key}', payload, ttl) 
 
    async def get_cached_compare_result(self, key): 
        return await self._safe_get_json(f'compare:{key}') 
 
    async def append_message(self, session_id, role, content, extra=None): 
        await self.chat_repo.append_message(session_id, role, content, extra) 
 
    async def recent_messages(self, session_id, limit=20): 
        messages = await self.chat_repo.list_messages(session_id, limit=limit) 
        return [{'role': message.role, 'content': message.content, 'extra': message.extra or {}} for message in messages] 
