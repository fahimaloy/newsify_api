from fastapi import APIRouter
from cj36.api.v1 import users, categories, posts, system

# This is the name main.py expects → must be called "api_router"
api_router = APIRouter()

api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(posts.router, prefix="/posts", tags=["posts"])
