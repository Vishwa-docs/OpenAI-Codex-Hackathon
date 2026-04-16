from fastapi import FastAPI

from .api.router import api_router

app = FastAPI(
    title="Cloud Migration Cockpit API",
    version="0.1.0",
    description="Control-plane API for migration assessment, reporting, approvals, registry management, and local demo bootstrap.",
)
app.include_router(api_router)
