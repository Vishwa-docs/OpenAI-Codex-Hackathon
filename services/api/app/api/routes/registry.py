from fastapi import APIRouter, Depends

from ...dependencies import get_orchestrator
from ...domain.models import RegistryEntry
from ...services.orchestration import AssessmentOrchestrator

router = APIRouter()


@router.get("/registry-entries", response_model=list[RegistryEntry])
def registry_entries(
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> list[RegistryEntry]:
    return orchestrator.build_assessment("legacycart").registry_entries

