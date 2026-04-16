from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    checked_at: datetime


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="cloud-migration-cockpit-api",
        version="0.1.0",
        checked_at=datetime.now(tz=UTC),
    )

