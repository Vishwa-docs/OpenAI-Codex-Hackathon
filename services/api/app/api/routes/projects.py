from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from ...dependencies import get_orchestrator, get_report_exporter
from ...domain.models import (
    AgentRun,
    ApprovalRecord,
    ApprovalDecision,
    ArtifactFormat,
    AssessmentRun,
    AssessmentRunCreate,
    AuditEvent,
    ChatMessage,
    ChatMessageCreate,
    CloudConnection,
    CloudConnectionCreate,
    CostRoiSummary,
    DeploymentExecution,
    DeploymentExecutionRequest,
    DeploymentPlan,
    DependencyGraph,
    EvalRun,
    FactoryProposal,
    Finding,
    IntakeProfile,
    ObservabilityTrace,
    ProjectCreate,
    ProjectOverview,
    ProviderOption,
    RegistryEntry,
    Report,
    ReportArtifact,
    SourceConnection,
    SourceConnectionCreate,
    RiskComplianceSummary,
    Scenario,
    ScenarioDiff,
)
from ...services.orchestration import AssessmentOrchestrator
from ...services.reporting import ReportExporter

router = APIRouter()

@router.post("/projects", response_model=IntakeProfile, status_code=201)
def create_project(
    draft: ProjectCreate,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> IntakeProfile:
    return orchestrator.create_project(**draft.model_dump())


project_router = APIRouter(prefix="/projects/{project_id}")


def _assessment(orchestrator: AssessmentOrchestrator, project_id: str):
    try:
        return orchestrator.build_assessment(project_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown project: {project_id}") from exc


def _project_lookup(project_id: str, loader):
    try:
        return loader(project_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown project: {project_id}") from exc


@project_router.get("/overview", response_model=ProjectOverview)
def project_overview(
    project_id: str,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> ProjectOverview:
    return _assessment(orchestrator, project_id).overview


@project_router.get("/assessment", response_model=AssessmentRun)
def project_assessment(
    project_id: str,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> AssessmentRun:
    return _assessment(orchestrator, project_id).run


@project_router.get("/dependency-graph", response_model=DependencyGraph)
def dependency_graph(
    project_id: str,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> DependencyGraph:
    return _assessment(orchestrator, project_id).graph


@project_router.get("/findings", response_model=list[Finding])
def project_findings(
    project_id: str,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> list[Finding]:
    return _assessment(orchestrator, project_id).findings


@project_router.get("/provider-comparison", response_model=list[ProviderOption])
def provider_comparison(
    project_id: str,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> list[ProviderOption]:
    return _assessment(orchestrator, project_id).provider_options


@project_router.get("/cost-roi", response_model=CostRoiSummary)
def cost_roi(
    project_id: str,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> CostRoiSummary:
    return _assessment(orchestrator, project_id).cost_roi


@project_router.get("/risk-compliance", response_model=RiskComplianceSummary)
def risk_compliance(
    project_id: str,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> RiskComplianceSummary:
    return _assessment(orchestrator, project_id).risk_compliance


@project_router.get("/scenarios", response_model=list[Scenario])
def scenarios(
    project_id: str,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> list[Scenario]:
    return _assessment(orchestrator, project_id).scenarios


@project_router.get("/scenario-diffs", response_model=list[ScenarioDiff])
def scenario_diffs(
    project_id: str,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> list[ScenarioDiff]:
    return _project_lookup(project_id, orchestrator.list_scenario_diffs)


@project_router.get("/reports", response_model=list[Report])
def reports(
    project_id: str,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> list[Report]:
    return _assessment(orchestrator, project_id).reports


@project_router.get("/artifacts", response_model=list[ReportArtifact])
def artifacts(
    project_id: str,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> list[ReportArtifact]:
    return _assessment(orchestrator, project_id).artifacts


@project_router.get("/reports/{report_id}")
def report_detail(
    project_id: str,
    report_id: str,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> Report:
    bundle = _assessment(orchestrator, project_id)
    for report in bundle.reports:
        if report.id == report_id:
            return report
    raise HTTPException(status_code=404, detail=f"Unknown report: {report_id}")


@project_router.get("/reports/{report_id}/export")
def export_report(
    project_id: str,
    report_id: str,
    format: ArtifactFormat = Query(default="pdf"),
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
    exporter: ReportExporter = Depends(get_report_exporter),
) -> Response:
    bundle = _assessment(orchestrator, project_id)
    report = next((item for item in bundle.reports if item.id == report_id), None)
    if report is None:
        raise HTTPException(status_code=404, detail=f"Unknown report: {report_id}")
    payload, media_type = exporter.export(report, format)
    extension = "pdf" if format == "pdf" else "md" if format == "markdown" else "json"
    headers = {"Content-Disposition": f'attachment; filename="{report_id}.{extension}"'}
    return Response(content=payload, media_type=media_type, headers=headers)


@project_router.get("/source-connections", response_model=list[SourceConnection])
def source_connections(
    project_id: str,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> list[SourceConnection]:
    return _project_lookup(project_id, orchestrator.list_source_connections)


@project_router.post("/source-connections", response_model=SourceConnection, status_code=201)
def create_source_connection(
    project_id: str,
    draft: SourceConnectionCreate,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> SourceConnection:
    return _project_lookup(project_id, lambda pid: orchestrator.create_source_connection(pid, draft))


@project_router.get("/cloud-connections", response_model=list[CloudConnection])
def cloud_connections(
    project_id: str,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> list[CloudConnection]:
    return _project_lookup(project_id, orchestrator.list_cloud_connections)


@project_router.post("/cloud-connections", response_model=CloudConnection, status_code=201)
def create_cloud_connection(
    project_id: str,
    draft: CloudConnectionCreate,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> CloudConnection:
    return _project_lookup(project_id, lambda pid: orchestrator.create_cloud_connection(pid, draft))


@project_router.get("/assessment-runs", response_model=list[AssessmentRun])
def assessment_runs(
    project_id: str,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> list[AssessmentRun]:
    return _project_lookup(project_id, orchestrator.list_assessment_runs)


@project_router.post("/assessment-runs", response_model=AssessmentRun, status_code=201)
def create_assessment_run(
    project_id: str,
    request: AssessmentRunCreate,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> AssessmentRun:
    return _project_lookup(project_id, lambda pid: orchestrator.create_assessment_run(pid, request))


@project_router.get("/agent-runs", response_model=list[AgentRun])
def agent_runs(
    project_id: str,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> list[AgentRun]:
    return _project_lookup(project_id, orchestrator.list_agent_runs)


@project_router.get("/eval-runs", response_model=list[EvalRun])
def eval_runs(
    project_id: str,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> list[EvalRun]:
    return _project_lookup(project_id, orchestrator.list_eval_runs)


@project_router.get("/factory-proposals", response_model=list[FactoryProposal])
def factory_proposals(
    project_id: str,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> list[FactoryProposal]:
    return _project_lookup(project_id, orchestrator.list_factory_proposals)


@project_router.get("/chat/messages", response_model=list[ChatMessage])
def chat_messages(
    project_id: str,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> list[ChatMessage]:
    return _project_lookup(project_id, orchestrator.list_chat_messages)


@project_router.post("/chat/messages", response_model=ChatMessage, status_code=201)
def create_chat_message(
    project_id: str,
    draft: ChatMessageCreate,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> ChatMessage:
    return _project_lookup(project_id, lambda pid: orchestrator.create_chat_message(pid, draft))


@project_router.get("/approvals", response_model=list[ApprovalRecord])
def approvals(
    project_id: str,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> list[ApprovalRecord]:
    return _assessment(orchestrator, project_id).approvals


@project_router.post("/approvals/{approval_id}/decision", response_model=ApprovalRecord)
def decide_approval(
    project_id: str,
    approval_id: str,
    decision: ApprovalDecision,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> ApprovalRecord:
    try:
        return orchestrator.decide_approval(project_id, approval_id, decision)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown approval: {approval_id}") from exc


@project_router.get("/audit-events", response_model=list[AuditEvent])
def audit_events(
    project_id: str,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> list[AuditEvent]:
    return _assessment(orchestrator, project_id).audit_events


@project_router.get("/registry-entries", response_model=list[RegistryEntry])
def project_registry_entries(
    project_id: str,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> list[RegistryEntry]:
    return _assessment(orchestrator, project_id).registry_entries


@project_router.get("/intake", response_model=IntakeProfile)
def intake_profile(
    project_id: str,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> IntakeProfile:
    return _project_lookup(project_id, orchestrator.get_intake_profile)


@project_router.get("/observability-traces", response_model=list[ObservabilityTrace])
def observability_traces(
    project_id: str,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> list[ObservabilityTrace]:
    return _project_lookup(project_id, orchestrator.list_observability_traces)


@project_router.get("/deployment-plan", response_model=DeploymentPlan)
def deployment_plan(
    project_id: str,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> DeploymentPlan:
    return _project_lookup(project_id, orchestrator.get_deployment_plan)


@project_router.post("/deployment-executions", response_model=DeploymentExecution, status_code=201)
def deployment_execution(
    project_id: str,
    request: DeploymentExecutionRequest,
    orchestrator: AssessmentOrchestrator = Depends(get_orchestrator),
) -> DeploymentExecution:
    try:
        return orchestrator.execute_deployment(project_id, request)
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


router.include_router(project_router)
