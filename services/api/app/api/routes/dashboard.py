from fastapi import APIRouter, Depends

from ...dependencies import get_orchestrator
from ...domain.models import DashboardSummary
from ...services.orchestration import AssessmentOrchestrator

router = APIRouter()


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> DashboardSummary:
    return orchestrator.get_dashboard_summary()

