from fastapi import FastAPI

from .api.router import api_router


app = FastAPI(
    title="Cloud Migration Cockpit API",
    version="0.1.0",
    description="Deterministic orchestration API for seeded migration assessment, reporting, approvals, and registry surfaces.",
)
app.include_router(api_router)

