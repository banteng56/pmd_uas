import asyncpg
import logging
from core.config import settings

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        self.pool = None
    
    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(settings.DATABASE_URL)
            await self.create_table()
            logger.info("Connected to PostgreSQL")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    async def create_table(self):
        pass  
    
    async def save_prediction(self, url: str, content: str, mlp_label, hmm_label):
        query = """
        UPDATE articles 
        SET mlp = $2, hmm = $3
        WHERE url = $1
        """
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute(query, url, mlp_label, hmm_label)
            logger.info(f"Updated articles table: {url}")
        except Exception as e:
            logger.error(f"Database update error: {e}")
    
    async def close(self):
        if self.pool:
            await self.pool.close()