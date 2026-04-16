from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from ...dependencies import get_orchestrator
from ...domain.models import ProjectCreate, ProjectOverview, WorkspaceContext
from ...services.orchestration import AssessmentOrchestrator

router = APIRouter(prefix="/workspaces/{workspace_id}")


def _workspace_lookup(workspace_id: str, loader):
    try:
        return loader(workspace_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown workspace: {workspace_id}") from exc


@router.get("/context", response_model=WorkspaceContext)
def workspace_context(
    workspace_id: str,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> WorkspaceContext:
    return _workspace_lookup(workspace_id, orchestrator.get_workspace_context)


@router.get("/projects", response_model=list[ProjectOverview])
def workspace_projects(
    workspace_id: str,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> list[ProjectOverview]:
    return _workspace_lookup(workspace_id, orchestrator.list_workspace_projects)


@router.post("/projects", response_model=ProjectOverview, status_code=status.HTTP_201_CREATED)
def create_workspace_project(
    workspace_id: str,
    draft: ProjectCreate,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> ProjectOverview:
    return _workspace_lookup(workspace_id, lambda target_workspace_id: orchestrator.create_workspace_project(target_workspace_id, draft))
