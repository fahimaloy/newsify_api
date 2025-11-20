from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlmodel import SQLModel
from cj36.core.config import settings
from cj36.api.v1.router import api_router
from cj36.dependencies import engine


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title="cj36",
    version="0.1.0",
    description="Production-ready FastAPI project",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {"message": "cj36 API is running!"}
