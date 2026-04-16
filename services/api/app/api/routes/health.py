from datetime import UTC, datetime

from fastapi import APIRouter

from ...core.settings import get_settings
from ...domain.models import ApiModel


class HealthResponse(ApiModel):
    status: str
    service: str
    version: str
    app_mode: str
    default_workspace_id: str
    desktop_download_url: str
    desktop_available: bool
    checked_at: datetime


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service="cloud-migration-cockpit-api",
        version="0.1.0",
        app_mode=settings.app_mode,
        default_workspace_id=settings.default_workspace_id,
        desktop_download_url=settings.desktop_download_url,
        desktop_available=settings.desktop_build_path.exists(),
        checked_at=datetime.now(tz=UTC),
    )
