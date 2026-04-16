from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


def to_camel(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        use_enum_values=True,
    )


Severity = Literal["critical", "high", "medium", "low"]
ApprovalState = Literal["not_required", "pending", "approved", "rejected"]
RunStatus = Literal["queued", "running", "succeeded", "failed"]
ReportKind = Literal[
    "executive_summary",
    "technical_dossier",
    "cost_report",
    "risk_report",
    "architecture_recommendation",
    "migration_wave_plan",
    "cutover_rollback",
    "operations_checklist",
    "roadmap",
    "terraform",
    "diagram",
]
ArtifactFormat = Literal["json", "markdown", "pdf", "mermaid", "hcl"]
RegistryKind = Literal["agent", "tool", "connector"]
RegistryStatus = Literal["enabled", "disabled", "proposed"]
ConnectionStatus = Literal["connected", "needs_attention", "needs_configuration", "proposed", "disabled"]
PipelineStatus = Literal["queued", "running", "blocked", "succeeded", "failed"]
CredentialKind = Literal["token", "oauth", "assumed_role", "access_key", "none"]
PipelineKey = Literal[
    "intake_clarification",
    "codebase_discovery",
    "architecture_analysis",
    "security_readiness",
    "hosting_fit_recommendation",
    "migration_strategy",
    "infra_plan_generation",
    "evaluation_critique",
    "deployment_readiness",
    "aws_execution",
    "post_deploy_validation",
]
TenantMode = Literal["demo", "standard"]


class EvidenceLocator(ApiModel):
    line_start: int | None = None
    line_end: int | None = None


class EvidenceReference(ApiModel):
    id: str
    source_type: Literal["file", "log", "manifest", "command_output"]
    source_uri: str
    excerpt: str
    locator: EvidenceLocator | None = None
    confidence: float


class Finding(ApiModel):
    id: str
    title: str
    category: str
    severity: Severity
    confidence: float
    summary: str
    recommendation: str
    evidence: list[EvidenceReference]


class Recommendation(ApiModel):
    id: str
    title: str
    summary: str
    confidence: float
    rationale: str
    effort: Literal["small", "medium", "large"]
    impact: Literal["high", "medium", "low"]
    evidence: list[EvidenceReference] = Field(default_factory=list)


class DependencyNode(ApiModel):
    id: str
    label: str
    kind: Literal["service", "job", "database", "storage", "external_api", "pipeline"]
    environment: Literal["legacy", "target"]
    status: Literal["observed", "at_risk", "planned"]
    x: float
    y: float


class DependencyEdge(ApiModel):
    id: str
    source: str
    target: str
    relation: Literal[
        "depends_on",
        "calls",
        "writes_to",
        "reads_from",
        "deployed_via",
        "schedules",
    ]


class ScenarioOutcome(ApiModel):
    readiness: int
    risk_delta: str
    cost_delta: str
    summary: str


class Scenario(ApiModel):
    id: str
    name: str
    description: str
    assumption_set: list[str]
    outcome: ScenarioOutcome


class ScenarioDiff(ApiModel):
    baseline_scenario_id: str
    compared_scenario_id: str
    readiness_delta: int
    risk_shift: str
    cost_shift: str
    summary: str


class ProviderOption(ApiModel):
    id: Literal["aws", "gcp", "azure"]
    name: str
    score: int
    best_for: str
    tradeoffs: list[str]
    rationale: str
    confidence: float
    evidence: list[EvidenceReference]


class ReportArtifact(ApiModel):
    id: str
    kind: ReportKind
    title: str
    format: ArtifactFormat
    description: str
    updated_at: datetime


class ReportSection(ApiModel):
    title: str
    body: str
    citations: list[EvidenceReference] = Field(default_factory=list)


class Report(ApiModel):
    id: str
    kind: ReportKind
    title: str
    summary: str
    confidence: float
    sections: list[ReportSection]
    generated_at: datetime
    artifact_ids: list[str]


class ApprovalRecord(ApiModel):
    id: str
    phase: str
    state: ApprovalState
    requested_by: str
    approver: str | None = None
    comment: str | None = None
    decided_at: datetime | None = None


class ApprovalDecision(ApiModel):
    decision: Literal["approved", "rejected"]
    actor: str
    comment: str


class AuditEvent(ApiModel):
    id: str
    actor: str
    action: str
    entity_type: str
    entity_id: str
    created_at: datetime
    metadata: dict[str, str] | None = None


class RegistryEntry(ApiModel):
    id: str
    name: str
    kind: RegistryKind
    status: RegistryStatus
    required_permissions: list[str]
    rationale: str
    version: str
    proposed_by: str
    enabled: bool


class CredentialRef(ApiModel):
    id: str
    kind: CredentialKind
    label: str
    redacted_value: str
    expires_at: datetime | None = None


class SourceConnection(ApiModel):
    id: str
    kind: Literal["local_directory", "github", "azure_repos"]
    name: str
    status: ConnectionStatus
    mode: Literal["read_only", "discovery", "approval_gated"]
    target: str
    branch: str | None = None
    last_sync_at: datetime | None = None
    credential_ref: CredentialRef
    notes: list[str]


class SourceConnectionCreate(ApiModel):
    kind: Literal["local_directory", "github", "azure_repos"]
    name: str
    target: str
    branch: str | None = None
    mode: Literal["read_only", "discovery", "approval_gated"] = "discovery"
    credential_label: str
    credential_kind: CredentialKind
    notes: list[str] = Field(default_factory=list)


class CloudConnection(ApiModel):
    id: str
    provider: Literal["aws", "gcp", "azure"]
    name: str
    status: ConnectionStatus
    mode: Literal["discovery", "dry_run", "approval_gated"]
    account_label: str
    region_scope: list[str]
    credential_ref: CredentialRef
    notes: list[str]


class CloudConnectionCreate(ApiModel):
    provider: Literal["aws", "gcp", "azure"]
    name: str
    account_label: str
    region_scope: list[str]
    mode: Literal["discovery", "dry_run", "approval_gated"] = "dry_run"
    credential_label: str
    credential_kind: CredentialKind
    notes: list[str] = Field(default_factory=list)


class PipelineSummary(ApiModel):
    pipeline_key: PipelineKey
    title: str
    status: PipelineStatus
    summary: str
    plain_language_summary: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class FactoryProposal(ApiModel):
    id: str
    name: str
    kind: RegistryKind
    status: Literal["proposed"]
    rationale: str
    required_permissions: list[str]
    prompt_version: str
    scaffold_files: list[str]
    approval_required: bool


class ChatMessage(ApiModel):
    id: str
    role: Literal["ai", "human", "system"]
    author: str
    created_at: datetime
    content: str


class ChatMessageCreate(ApiModel):
    role: Literal["ai", "human", "system"]
    author: str
    content: str


class IntakeProfile(ApiModel):
    id: str
    project_id: str
    name: str
    client_name: str
    source_kind: Literal["local_directory", "github", "azure_repos"]
    source_target: str
    expected_users: int
    preferred_cloud: Literal["aws", "gcp", "azure"] = "aws"
    business_constraints: list[str] = Field(default_factory=list)
    compliance_notes: list[str] = Field(default_factory=list)
    credential_label: str
    credential_kind: CredentialKind
    founder_summary: str


class ProjectCreate(ApiModel):
    name: str
    client_name: str
    source_kind: Literal["local_directory", "github", "azure_repos"] | None = None
    source_target: str | None = None
    expected_users: int | None = Field(default=None, ge=1)
    preferred_cloud: Literal["aws", "gcp", "azure"] = "aws"
    business_constraints: list[str] = Field(default_factory=list)
    compliance_notes: list[str] = Field(default_factory=list)
    credential_label: str | None = None
    credential_kind: CredentialKind | None = None
    source_system: str | None = None
    target_system: str | None = None
    business_summary: str | None = None
    owner: str | None = None
    primary_region: str | None = None
    compliance_tags: list[str] = Field(default_factory=list)


class PlatformRecommendation(ApiModel):
    platform_key: Literal["vercel", "railway", "aws-ec2", "aws-ecs", "aws-lambda", "cloudflare-workers"]
    label: str
    fit_score: int
    best_for: str
    rationale: str
    plain_language_rationale: str
    tradeoffs: list[str]
    monthly_cost_estimate: str
    scaling_threshold: str
    execution_ready: bool = False


class DeploymentArtifact(ApiModel):
    id: str
    kind: Literal["terraform", "ansible", "checklist"]
    title: str
    summary: str
    preview: str


class DeploymentExecution(ApiModel):
    id: str
    provider: Literal["aws"]
    mode: Literal["dry_run", "apply"]
    status: RunStatus
    triggered_by: str
    summary: str
    created_at: datetime
    next_steps: list[str] = Field(default_factory=list)


class DeploymentExecutionRequest(ApiModel):
    provider: Literal["aws"]
    mode: Literal["dry_run", "apply"]
    triggered_by: str


class DeploymentPlan(ApiModel):
    project_id: str
    execution_state: Literal["blocked", "ready", "in_progress", "succeeded"]
    founder_summary: str
    recommended_platform: PlatformRecommendation
    platform_options: list[PlatformRecommendation]
    required_actions: list[str]
    artifacts: list[DeploymentArtifact]
    last_execution: DeploymentExecution | None = None


class ObservabilityTrace(ApiModel):
    id: str
    stage_key: PipelineKey
    agent_key: str
    title: str
    status: RunStatus
    summary: str
    confidence: float
    latency_ms: int
    evidence_count: int
    warnings: list[str] = Field(default_factory=list)
    evaluation_summary: str
    question_checkpoint: str | None = None


class AgentRun(ApiModel):
    id: str
    assessment_run_id: str
    agent_key: str
    display_name: str
    stage: Literal["intake", "discovery", "analysis", "planning", "critique", "reporting"]
    status: RunStatus
    critic: bool
    confidence: float
    summary: str
    evidence_count: int
    latency_ms: int
    warning_count: int
    retry_count: int
    started_at: datetime
    completed_at: datetime | None = None


class EvalMetric(ApiModel):
    metric_key: Literal[
        "citation_coverage",
        "unsupported_claim_rate",
        "recommendation_consistency",
        "cost_sanity",
        "latency",
        "policy_compliance",
    ]
    label: str
    score: int
    summary: str
    status: Literal["pass", "warn", "fail"]


class EvalRun(ApiModel):
    id: str
    assessment_run_id: str
    overall_score: int
    status: RunStatus
    completed_at: datetime
    metrics: list[EvalMetric]


class ProjectOverview(ApiModel):
    id: str
    name: str
    client_name: str
    readiness_score: int
    migration_decision: str
    confidence: float
    phase: str
    status: str
    recommended_provider: str


class UserProfile(ApiModel):
    id: str
    email: str
    name: str
    active_organization_id: str | None = None


class OrganizationSummary(ApiModel):
    id: str
    name: str
    slug: str
    mode: TenantMode


class WorkspaceSummary(ApiModel):
    id: str
    organization_id: str
    name: str
    slug: str
    mode: TenantMode
    project_count: int


class ClientAccountSummary(ApiModel):
    id: str
    workspace_id: str
    name: str
    industry: str
    primary_region: str
    compliance_tags: list[str] = Field(default_factory=list)


class WorkspaceContext(ApiModel):
    organization: OrganizationSummary
    workspace: WorkspaceSummary
    client_accounts: list[ClientAccountSummary]
    projects: list[ProjectOverview]


class DashboardSummary(ApiModel):
    active_projects: int
    pending_approvals: int
    open_findings: int
    report_exports: int
    top_projects: list[ProjectOverview]


class CostRoiSummary(ApiModel):
    annual_baseline_cost: int
    annual_target_cost: int
    migration_investment: int
    annual_savings: int
    payback_months: int
    roi_percent: int
    summary: str
    confidence: float
    assumptions: list[str]
    evidence: list[EvidenceReference]


class RiskItem(ApiModel):
    id: str
    severity: Severity
    domain: str
    title: str
    impact: str
    mitigation: str
    confidence: float
    evidence: list[EvidenceReference]


class RiskComplianceSummary(ApiModel):
    overall_risk: Literal["critical", "high", "moderate", "low"]
    compliance_frameworks: list[str]
    data_residency: str
    operational_readiness: str
    risks: list[RiskItem]
    summary: str
    confidence: float


class DependencyGraph(ApiModel):
    nodes: list[DependencyNode]
    edges: list[DependencyEdge]
    generated_at: datetime
    summary: str


class AgentOutput(ApiModel):
    agent_key: str
    display_name: str
    status: RunStatus
    confidence: float
    summary: str
    evidence: list[EvidenceReference]
    structured_output: dict[str, Any]
    limitations: list[str] = Field(default_factory=list)


class FinalRecommendation(ApiModel):
    decision: Literal["migrate_now", "migrate_partially", "defer", "rearchitect_first"]
    label: str
    confidence: float
    summary: str
    recommended_provider: str
    rationale: list[str]
    blockers: list[str]
    next_steps: list[str]
    evidence: list[EvidenceReference]


class AssessmentRun(ApiModel):
    id: str
    project_id: str
    status: RunStatus
    started_at: datetime
    completed_at: datetime
    mode: Literal["sync", "local_worker"]
    pipeline_summaries: list[PipelineSummary] = Field(default_factory=list)
    agent_outputs: list[AgentOutput]
    final_recommendation: FinalRecommendation


class AssessmentRunCreate(ApiModel):
    mode: Literal["sync", "local_worker"] = "local_worker"
    triggered_by: str


class ProjectSeed(ApiModel):
    overview: ProjectOverview
    evidence: list[EvidenceReference]
    findings: list[Finding]
    graph: DependencyGraph
    source_connections: list[SourceConnection]
    cloud_connections: list[CloudConnection]
    factory_proposals: list[FactoryProposal]
    chat_messages: list[ChatMessage]
    approvals: list[ApprovalRecord]
    audit_events: list[AuditEvent]
    registry_entries: list[RegistryEntry]
    reports: list[Report]
    artifacts: list[ReportArtifact]
    assessment_runs: list[AssessmentRun] = Field(default_factory=list)
    intake_profile: IntakeProfile | None = None
    deployment_plan: DeploymentPlan | None = None
    observability_traces: list[ObservabilityTrace] = Field(default_factory=list)
    deployment_executions: list[DeploymentExecution] = Field(default_factory=list)


class AssessmentBundle(ApiModel):
    run: AssessmentRun
    overview: ProjectOverview
    dashboard: DashboardSummary
    graph: DependencyGraph
    findings: list[Finding]
    provider_options: list[ProviderOption]
    cost_roi: CostRoiSummary
    risk_compliance: RiskComplianceSummary
    scenarios: list[Scenario]
    scenario_diffs: list[ScenarioDiff] = Field(default_factory=list)
    reports: list[Report]
    artifacts: list[ReportArtifact]
    approvals: list[ApprovalRecord]
    audit_events: list[AuditEvent]
    registry_entries: list[RegistryEntry]
