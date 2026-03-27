from fastapi import FastAPI  
from app.api.routes.chat import router as chat_router  
from app.api.routes.compare import router as compare_router  
from app.api.routes.recommend import router as recommend_router  
from app.core.config import settings  
from app.db.init_db import init_db  
from app.infra.redis_client import close_redis  
  
app = FastAPI(title='NovaTech Smart Shopping Agent', version='0.1.0')  
  
@app.get('/health')  
async def health():  
    return {'status': 'ok', 'app_name': settings.app_name}  
  
@app.on_event('startup')  
async def startup_event():  
    await init_db()  
  
app.include_router(chat_router, prefix = settings.api_v1_prefix)  
app.include_router(compare_router, prefix = settings.api_v1_prefix)  
app.include_router(recommend_router, prefix = settings.api_v1_prefix)  
  
@app.on_event('shutdown')  
async def shutdown_event():  
    await close_redis() 
