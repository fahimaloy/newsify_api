from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from sqlmodel import SQLModel, Session
from cj36.core.config import settings
from cj36.api.v1.router import api_router
from cj36.dependencies import engine
from cj36.core.seed import seed_database
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from cj36.scheduler import start_scheduler, shutdown_scheduler
import time


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
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan,
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # HSTS for production
    if settings.ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response

# Rate Limiting Middleware (Simple implementation)
rate_limit_storage = {}

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Skip rate limiting for health checks and static files
    if request.url.path.startswith("/health") or request.url.path.startswith("/static"):
        return await call_next(request)
    
    client_ip = request.client.host if request.client else "unknown"
    current_time = time.time()
    
    # Clean old entries (older than 1 minute)
    rate_limit_storage[client_ip] = [
        timestamp for timestamp in rate_limit_storage.get(client_ip, [])
        if current_time - timestamp < 60
    ]
    
    # Check rate limit (100 requests per minute)
    if len(rate_limit_storage.get(client_ip, [])) >= 100:
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please try again later."}
        )
    
    # Add current request
    rate_limit_storage.setdefault(client_ip, []).append(current_time)
    
    return await call_next(request)

# CORS middleware with proper configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# GZip compression for responses
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Serve static files with cache headers
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return {"message": "cj36 API is running!", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "message": "API is running",
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT
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
