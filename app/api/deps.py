from app.db.session import AsyncSessionLocal 
 
async def get_db_session(): 
    async with AsyncSessionLocal() as session: 
        yield session
