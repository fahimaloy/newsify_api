import asyncpg
from cj36.core.config import settings

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            settings.db_url,
            min_size=5,
            max_size=20,
        )

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

db = Database()
