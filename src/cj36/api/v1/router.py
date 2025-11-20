from fastapi import APIRouter, Depends
from cj36.core.database import db
import asyncpg

# This is the name main.py expects → must be called "api_router"
api_router = APIRouter()


@api_router.get("/health")
async def health_check():
    db_status = "ok"
    try:
        async with db.pool.acquire() as connection:
            await connection.execute("SELECT 1")
    except (asyncpg.exceptions.PostgresError, ConnectionRefusedError) as e:
        db_status = f"error: {e}"

    return {
        "status": "healthy",
        "project": "CJ36-API",
        "database": db_status,
    }
