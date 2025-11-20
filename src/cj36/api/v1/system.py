from fastapi import APIRouter, Depends, status, Request
from sqlmodel import Session
from sqlalchemy import text
import psutil

from cj36.dependencies import get_db

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint.
    """
    try:
        # Check database connection
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"

    # System resource usage
    cpu_usage = psutil.cpu_percent()
    ram_usage = psutil.virtual_memory().percent

    return {
        "backend_status": "ok",
        "database_status": db_status,
        "system": {
            "cpu_usage_percent": cpu_usage,
            "ram_usage_percent": ram_usage,
        },
    }


@router.get("/routes")
def get_all_routes(request: Request):
    """
    Get all available API routes.
    """
    routes = []
    for route in request.app.routes:
        if hasattr(route, "methods"):
            routes.append(
                {
                    "path": route.path,
                    "name": route.name,
                    "methods": sorted(list(route.methods)),
                }
            )
    return routes
