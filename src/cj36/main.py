from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlmodel import SQLModel, Session
from cj36.core.config import settings
from cj36.api.v1.router import api_router
from cj36.dependencies import engine
from cj36.core.seed import seed_database


from cj36.scheduler import start_scheduler, shutdown_scheduler


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_db_and_tables()
    with Session(engine) as session:
        seed_database(session)
    
    # Start background scheduler for scheduled posts
    start_scheduler()
    
    yield
    
    # Shutdown
    shutdown_scheduler()


app = FastAPI(
    title="cj36",
    version="0.1.0",
    description="Production-ready FastAPI project",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware to allow frontend requests
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from fastapi.staticfiles import StaticFiles

app.include_router(api_router, prefix=settings.API_V1_STR)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return {"message": "cj36 API is running!"}


@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "message": "API is running",
        "version": "0.1.0"
    }


@app.get("/health/scheduler")
async def scheduler_health():
    """Check if the background scheduler is running"""
    from cj36.scheduler import scheduler
    
    jobs = []
    if scheduler.running:
        jobs = [
            {
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None
            }
            for job in scheduler.get_jobs()
        ]
    
    return {
        "scheduler_running": scheduler.running,
        "jobs": jobs,
        "status": "healthy" if scheduler.running else "stopped"
    }
