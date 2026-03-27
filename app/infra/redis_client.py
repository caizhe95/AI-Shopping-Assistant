from __future__ import annotations 
 
from redis.asyncio import from_url 
 
from app.core.config import settings 
 
_redis = None 
 
async def get_redis(): 
    global _redis 
    if _redis is None: 
        _redis = from_url(settings.redis_url, decode_responses=True) 
    return _redis 
 
async def close_redis(): 
    global _redis 
    if _redis is not None: 
        await _redis.aclose() 
