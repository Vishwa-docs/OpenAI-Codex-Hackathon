from fastapi import APIRouter

from .routes import dashboard, health, projects, registry

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router, tags=["health"])
api_router.include_router(dashboard.router, tags=["dashboard"])
api_router.include_router(projects.router, tags=["projects"])
api_router.include_router(registry.router, tags=["registry"])

