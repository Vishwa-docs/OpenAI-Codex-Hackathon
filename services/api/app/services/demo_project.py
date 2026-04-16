from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from services.worker.app.scanner import scan_legacycart

from ..domain.models import (
    ApprovalRecord,
    AuditEvent,
    ChatMessage,
    CloudConnection,
    CredentialRef,
    DependencyEdge,
    DependencyGraph,
    DependencyNode,
    EvidenceLocator,
    EvidenceReference,
    FactoryProposal,
    Finding,
    ProjectOverview,
    ProjectSeed,
    RegistryEntry,
    Report,
    ReportArtifact,
    ReportSection,
    SourceConnection,
)

AGENT_REGISTRY = [
    ("intake_normalizer", "Intake Normalizer Agent"),
    ("codebase_discovery", "Codebase Discovery Agent"),
    ("infra_manifest_analyzer", "Infra Manifest Analyzer Agent"),
    ("dependency_graph", "Dependency Graph Agent"),
    ("database_data_store", "Database & Data Store Analyzer Agent"),
    ("runtime_ops_readiness", "Runtime / Ops Readiness Agent"),
    ("security_secrets", "Security & Secrets Agent"),
    ("risk_compliance", "Risk & Compliance Agent"),
    ("cloud_recommendation", "Cloud Recommendation Agent"),
    ("cost_roi", "Cost & ROI Agent"),
    ("architecture_planner", "Architecture Planner Agent"),
    ("container_kubernetes", "Container / Kubernetes Planner Agent"),
    ("devops_pipeline", "DevOps Pipeline Agent"),
    ("scenario_what_if", "Scenario / What-if Agent"),
    ("report_composer", "Report Composer Agent"),
    ("executive_summary", "Executive Summary Agent"),
    ("tool_gap_detector", "Tool Gap Detector Agent"),
    ("tool_connector_scaffold", "Tool / Connector Scaffold Agent"),
    ("safety_critic", "Safety Critic Agent"),
    ("citation_evidence_critic", "Citation / Evidence Critic Agent"),
    ("final_recommendation_aggregator", "Final Recommendation Aggregator"),
]

COMPONENT_POSITIONS: dict[str, tuple[float, float]] = {
    "frontend": (120, 40),
    "backend": (120, 140),
    "jobs": (120, 250),
    "database": (360, 140),
    "storage": (370, 50),
    "pipeline": (360, 250),
    "integration": (600, 140),
}


def build_demo_project_seed(now: datetime | None = None) -> ProjectSeed:
    generated_at = (now or datetime.now(UTC)).replace(microsecond=0)
    scan = scan_legacycart(_legacycart_root())

    evidence = [_map_evidence(item) for item in scan.evidence]
    evidence_by_id = {item.id: item for item in evidence}
    findings = [_map_finding(item, evidence_by_id) for item in scan.findings]
    graph = _build_dependency_graph(scan, generated_at)
    overview = _build_overview(scan)
    source_connections = _build_source_connections(generated_at)
    cloud_connections = _build_cloud_connections()
    factory_proposals = _build_factory_proposals(scan)
    registry_entries = _build_registry_entries()
    artifacts = _build_artifacts(generated_at)
    reports = _build_reports(
        generated_at=generated_at,
        overview=overview,
        findings=findings,
        evidence_by_id=evidence_by_id,
        artifacts=artifacts,
        provider=overview.recommended_provider,
        graph=graph,
    )
    approvals = _build_approvals()
    audit_events = _build_audit_events(scan, generated_at)
    chat_messages = _build_chat_messages(generated_at, overview, findings)

    return ProjectSeed(
        overview=overview,
        evidence=evidence,
        findings=findings,
        graph=graph,
        source_connections=source_connections,
        cloud_connections=cloud_connections,
        factory_proposals=factory_proposals,
        chat_messages=chat_messages,
        approvals=approvals,
        audit_events=audit_events,
        registry_entries=registry_entries,
        reports=reports,
        artifacts=artifacts,
    )


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _legacycart_root() -> Path:
    return _repo_root() / "demo-systems" / "legacycart"


def _map_evidence(item) -> EvidenceReference:
    locator = None
    if item.locator:
        locator = EvidenceLocator(
            line_start=int(item.locator.get("lineStart")) if item.locator.get("lineStart") else None,
            line_end=int(item.locator.get("lineEnd")) if item.locator.get("lineEnd") else None,
        )
    source_type: Literal["file", "log", "manifest", "command_output"] = (
        item.source_type if item.source_type in {"file", "log", "manifest"} else "command_output"
    )
    return EvidenceReference(
        id=item.id,
        source_type=source_type,
        source_uri=item.source_uri,
        excerpt=item.excerpt,
        locator=locator,
        confidence=item.confidence,
    )


def _map_finding(item, evidence_by_id: dict[str, EvidenceReference]) -> Finding:
    return Finding(
        id=item.id,
        title=item.title,
        category=item.category,
        severity=item.severity,
        confidence=item.confidence,
        summary=item.summary,
        recommendation=item.recommendation,
        evidence=[evidence_by_id[evidence_id] for evidence_id in item.evidence_ids if evidence_id in evidence_by_id],
    )


def _build_dependency_graph(scan, generated_at: datetime) -> DependencyGraph:
    node_kind_map: dict[
        str,
        Literal["service", "job", "database", "storage", "external_api", "pipeline"],
    ] = {
        "frontend": "service",
        "service": "service",
        "job": "job",
        "database": "database",
        "storage": "storage",
        "pipeline": "pipeline",
        "integration": "external_api",
    }
    nodes: list[DependencyNode] = []
    for component in scan.components:
        x, y = COMPONENT_POSITIONS.get(component.id, (120.0, float(100 + len(nodes) * 60)))
        status: Literal["observed", "at_risk", "planned"] = (
            "observed" if component.kind == "integration" else "at_risk"
        )
        nodes.append(
            DependencyNode(
                id=component.id,
                label=component.name,
                kind=node_kind_map[component.kind],
                environment="legacy",
                status=status,
                x=x,
                y=y,
            )
        )

    provider = str(scan.summary.provider_ranking[0]["provider"])
    nodes.append(
        DependencyNode(
            id="target-platform",
            label=f"{provider} Target Platform",
            kind="service",
            environment="target",
            status="planned",
            x=640,
            y=40,
        )
    )

    edges = [
        DependencyEdge(
            id=item.id,
            source=item.source,
            target=item.target,
            relation=item.relation,
        )
        for item in scan.dependencies
    ]

    return DependencyGraph(
        nodes=nodes,
        edges=edges,
        generated_at=generated_at,
        summary=(
            f"{scan.target_name} is composed of {len(scan.components)} observed components, "
            f"{len(scan.dependencies)} dependency edges, and a planned {provider} target platform."
        ),
    )


def _build_overview(scan) -> ProjectOverview:
    decision_map = {
        "migrate now": "Migrate now",
        "migrate partially": "Migrate partially",
        "defer until blockers are remediated": "Defer until blockers are remediated",
        "re-architect first": "Re-architect first",
    }
    decision = decision_map.get(scan.summary.recommendation, scan.summary.recommendation.title())
    return ProjectOverview(
        id=scan.project_id or "legacycart",
        name=f"{scan.target_name} Modernization",
        client_name="Northstar Retail Group",
        readiness_score=scan.summary.readiness_score,
        migration_decision=decision,
        confidence=scan.summary.confidence,
        phase="assessment",
        status="attention_required" if scan.summary.blocker_count > 0 else "ready",
        recommended_provider=str(scan.summary.provider_ranking[0]["provider"]),
    )


def _build_source_connections(generated_at: datetime) -> list[SourceConnection]:
    return [
        SourceConnection(
            id="source-local-directory",
            kind="local_directory",
            name="Local directory",
            status="connected",
            mode="read_only",
            target="demo-systems/legacycart",
            last_sync_at=generated_at,
            credential_ref=CredentialRef(
                id="cred-local-directory",
                kind="none",
                label="Read-only local scan",
                redacted_value="none",
            ),
            notes=[
                "Primary demo workload is scanned from the local demo-system directory.",
                "Evidence is gathered from the real repository files, manifests, and logs in that path.",
            ],
        ),
        SourceConnection(
            id="source-github",
            kind="github",
            name="GitHub repository",
            status="needs_configuration",
            mode="discovery",
            target="github.com/<org>/<repo>",
            branch="main",
            credential_ref=CredentialRef(
                id="cred-github",
                kind="oauth",
                label="GitHub App or PAT",
                redacted_value="not-configured",
            ),
            notes=[
                "Live read-only sync is available once GitHub credentials are supplied.",
                "Until then, the connector remains unvalidated and does not claim connected state.",
            ],
        ),
        SourceConnection(
            id="source-azure-repos",
            kind="azure_repos",
            name="Azure Repos",
            status="needs_configuration",
            mode="discovery",
            target="dev.azure.com/<org>/<project>/<repo>",
            branch="main",
            credential_ref=CredentialRef(
                id="cred-azure-repos",
                kind="oauth",
                label="Azure DevOps OAuth or PAT",
                redacted_value="not-configured",
            ),
            notes=[
                "Live read-only sync is available once Azure DevOps credentials are supplied.",
                "The connector stays unvalidated until that configuration exists.",
            ],
        ),
    ]


def _build_cloud_connections() -> list[CloudConnection]:
    return [
        CloudConnection(
            id="cloud-aws",
            provider="aws",
            name="AWS discovery workspace",
            status="needs_configuration",
            mode="discovery",
            account_label="Awaiting sandbox role",
            region_scope=["us-east-1"],
            credential_ref=CredentialRef(
                id="cred-aws",
                kind="assumed_role",
                label="AWS discovery role",
                redacted_value="not-configured",
            ),
            notes=[
                "AWS is the first live discovery and dry-run execution target.",
                "STS role assumption must be configured before any inventory claim is surfaced as connected.",
            ],
        ),
        CloudConnection(
            id="cloud-gcp",
            provider="gcp",
            name="GCP advisory workspace",
            status="needs_configuration",
            mode="discovery",
            account_label="Awaiting service account",
            region_scope=["us-central1"],
            credential_ref=CredentialRef(
                id="cred-gcp",
                kind="token",
                label="GCP advisory credential",
                redacted_value="not-configured",
            ),
            notes=[
                "GCP remains a recommendation target in v1.",
                "Live discovery is intentionally disabled until a later implementation pass and credential setup.",
            ],
        ),
        CloudConnection(
            id="cloud-azure",
            provider="azure",
            name="Azure advisory workspace",
            status="needs_configuration",
            mode="discovery",
            account_label="Awaiting service principal",
            region_scope=["eastus"],
            credential_ref=CredentialRef(
                id="cred-azure-cloud",
                kind="oauth",
                label="Azure advisory credential",
                redacted_value="not-configured",
            ),
            notes=[
                "Azure remains a recommendation target in v1.",
                "Live discovery and execution are not claimed until explicit credential and adapter support is in place.",
            ],
        ),
    ]


def _build_factory_proposals(scan) -> list[FactoryProposal]:
    proposals = [
        FactoryProposal(
            id="proposal-certificate-inventory",
            name="Certificate inventory collector",
            kind="tool",
            status="proposed",
            rationale=(
                "The current evidence set is strong on application and pipeline posture, but ingress certificate "
                "inventory and DNS readiness still need a dedicated collector."
            ),
            required_permissions=["dns:read", "network:read"],
            prompt_version="2026-04-16-cert-inventory-v1",
            scaffold_files=[
                "services/worker/app/tools/certificate_inventory.py",
                "services/api/tests/test_certificate_inventory.py",
            ],
            approval_required=True,
        )
    ]
    if any(item.kind == "azure_repos" for item in scan.connector_handoffs):
        proposals.append(
            FactoryProposal(
                id="proposal-azure-repos-hardening",
                name="Azure Repos live ingestion hardening",
                kind="connector",
                status="proposed",
                rationale=(
                    "Azure Repos exists in the connector contract, but a production-grade enterprise rollout still "
                    "needs credential rotation, branch policy awareness, and richer sync diagnostics."
                ),
                required_permissions=["repo:read", "oauth:azure-devops"],
                prompt_version="2026-04-16-azure-repos-hardening-v1",
                scaffold_files=[
                    "services/worker/app/connectors/azure_repos.py",
                    "services/api/tests/test_azure_repos_live.py",
                ],
                approval_required=True,
            )
        )
    return proposals


def _build_registry_entries() -> list[RegistryEntry]:
    entries = [
        RegistryEntry(
            id=f"reg-{key}",
            name=name,
            kind="agent",
            status="enabled",
            required_permissions=["project:read"],
            rationale="Specialist assessment and planning agent available in the control plane registry.",
            version="1.0.0",
            proposed_by="system",
            enabled=True,
        )
        for key, name in AGENT_REGISTRY
    ]
    entries.extend(
        [
            RegistryEntry(
                id="reg-aws-execution-adapter",
                name="AWS Dry-Run Execution Adapter",
                kind="connector",
                status="disabled",
                required_permissions=["cloud:read", "cloud:plan", "approval:execution"],
                rationale="Prepared for stage 3 execution, but disabled until credentials and approvals are in place.",
                version="0.1.0",
                proposed_by="system",
                enabled=False,
            ),
            RegistryEntry(
                id="reg-certificate-inventory",
                name="Certificate Inventory Collector",
                kind="tool",
                status="proposed",
                required_permissions=["dns:read", "network:read"],
                rationale="Proposed by the tool-gap workflow to close TLS and ingress evidence gaps.",
                version="0.1.0-proposed",
                proposed_by="Tool Gap Detector Agent",
                enabled=False,
            ),
        ]
    )
    return entries


def _build_artifacts(generated_at: datetime) -> list[ReportArtifact]:
    return [
        ReportArtifact(
            id="artifact-executive-summary",
            kind="executive_summary",
            title="Executive Summary PDF",
            format="pdf",
            description="Stakeholder summary of readiness, blockers, confidence, and next-step approvals.",
            updated_at=generated_at,
        ),
        ReportArtifact(
            id="artifact-technical-dossier",
            kind="technical_dossier",
            title="Technical Migration Dossier",
            format="markdown",
            description="Evidence-backed technical findings, dependency notes, and remediation guidance.",
            updated_at=generated_at,
        ),
        ReportArtifact(
            id="artifact-cost-roi",
            kind="cost_report",
            title="Cost and ROI Pack",
            format="json",
            description="Financial framing for remediation, platform spend, and payback assumptions.",
            updated_at=generated_at,
        ),
        ReportArtifact(
            id="artifact-architecture",
            kind="architecture_recommendation",
            title="Architecture Recommendation",
            format="pdf",
            description="Target landing-zone architecture and phased migration direction.",
            updated_at=generated_at,
        ),
        ReportArtifact(
            id="artifact-wave-plan",
            kind="migration_wave_plan",
            title="Migration Wave Plan",
            format="mermaid",
            description="Wave-by-wave migration and remediation sequence.",
            updated_at=generated_at,
        ),
        ReportArtifact(
            id="artifact-cutover-rollback",
            kind="cutover_rollback",
            title="Cutover and Rollback Playbook",
            format="pdf",
            description="Controlled cutover and rollback guidance grounded in current blockers.",
            updated_at=generated_at,
        ),
        ReportArtifact(
            id="artifact-ops-checklist",
            kind="operations_checklist",
            title="Operations Readiness Checklist",
            format="markdown",
            description="Monitoring, backup, DR, ownership, and runbook readiness checklist.",
            updated_at=generated_at,
        ),
        ReportArtifact(
            id="artifact-terraform",
            kind="terraform",
            title="Terraform Starter",
            format="hcl",
            description="Initial IaC scaffold for landing zone, managed database, and object storage.",
            updated_at=generated_at,
        ),
        ReportArtifact(
            id="artifact-diagram",
            kind="diagram",
            title="Target Architecture Diagram",
            format="mermaid",
            description="Architecture diagram for the recommended provider path.",
            updated_at=generated_at,
        ),
    ]


def _build_reports(
    *,
    generated_at: datetime,
    overview: ProjectOverview,
    findings: list[Finding],
    evidence_by_id: dict[str, EvidenceReference],
    artifacts: list[ReportArtifact],
    provider: str,
    graph: DependencyGraph,
) -> list[Report]:
    top_findings = findings[:3]
    top_evidence = [evidence for finding in top_findings for evidence in finding.evidence[:1]]
    component_labels = ", ".join(node.label for node in graph.nodes if node.environment == "legacy")
    artifact_map = {artifact.kind: artifact.id for artifact in artifacts}

    return [
        Report(
            id="report-executive",
            kind="executive_summary",
            title="Executive Migration Summary",
            summary=(
                f"{overview.migration_decision}. {provider} is the leading target once the highest-risk blockers are remediated."
            ),
            confidence=overview.confidence,
            generated_at=generated_at,
            artifact_ids=[artifact_map["executive_summary"]],
            sections=[
                ReportSection(
                    title="Decision",
                    body=(
                        f"Readiness is currently {overview.readiness_score}/100. The immediate recommendation is "
                        f"{overview.migration_decision.lower()} because critical and high-severity blockers remain open."
                    ),
                    citations=top_evidence[:2],
                ),
                ReportSection(
                    title="Why Now Is Not Yet Move Day",
                    body="The most important blockers are concentrated in secrets handling, logging hygiene, and operational coupling.",
                    citations=top_evidence,
                ),
                ReportSection(
                    title="Provider Direction",
                    body=(
                        f"{provider} is the current leading target because the workload benefits from managed database, "
                        "object storage, IAM guardrails, and staged modernization options."
                    ),
                    citations=top_evidence[:2],
                ),
            ],
        ),
        Report(
            id="report-technical",
            kind="technical_dossier",
            title="Technical Migration Dossier",
            summary="Current-state technical dossier assembled from the real demo-system scan and normalized evidence store.",
            confidence=overview.confidence,
            generated_at=generated_at,
            artifact_ids=[artifact_map["technical_dossier"]],
            sections=[
                ReportSection(
                    title="Current Estate",
                    body=f"Observed legacy components: {component_labels}.",
                    citations=top_evidence[:2],
                ),
                ReportSection(
                    title="Primary Blockers",
                    body=" ".join(
                        f"{finding.title}: {finding.summary}" for finding in top_findings
                    ),
                    citations=top_evidence,
                ),
            ],
        ),
        Report(
            id="report-cost",
            kind="cost_report",
            title="Cost and ROI Pack",
            summary="Cost framing for staged migration, remediation work, and long-term operational savings.",
            confidence=max(0.75, overview.confidence - 0.05),
            generated_at=generated_at,
            artifact_ids=[artifact_map["cost_report"]],
            sections=[
                ReportSection(
                    title="Cost Drivers",
                    body=(
                        "Primary cost drivers are legacy operations overhead, self-managed database effort, "
                        "shared storage handling, and manual batch-job support."
                    ),
                    citations=top_evidence[:2],
                ),
                ReportSection(
                    title="ROI Shape",
                    body=(
                        "A remediation-first or strangler-style program increases short-term investment but "
                        "improves long-term payback by reducing operational toil and security debt."
                    ),
                    citations=top_evidence[1:3],
                ),
            ],
        ),
        Report(
            id="report-risk",
            kind="risk_report",
            title="Security and Compliance Pack",
            summary="Risk register focused on secrets, logging exposure, transport posture, and operational coupling.",
            confidence=overview.confidence,
            generated_at=generated_at,
            artifact_ids=[],
            sections=[
                ReportSection(
                    title="Risk Register",
                    body=" ".join(
                        f"{finding.title}: {finding.recommendation}" for finding in top_findings
                    ),
                    citations=top_evidence,
                ),
                ReportSection(
                    title="Control Priorities",
                    body=(
                        "Prioritize vault-backed secrets, log redaction, TLS enforcement, restore testing, "
                        "and approval-gated delivery identities before planning closes."
                    ),
                    citations=top_evidence[:2],
                ),
            ],
        ),
        Report(
            id="report-architecture",
            kind="architecture_recommendation",
            title="Architecture Recommendation",
            summary=f"Recommended target shape: {provider} landing zone, managed PostgreSQL, and object-storage-backed file flows.",
            confidence=max(0.78, overview.confidence - 0.03),
            generated_at=generated_at,
            artifact_ids=[artifact_map["architecture_recommendation"], artifact_map["diagram"], artifact_map["terraform"]],
            sections=[
                ReportSection(
                    title="Target Shape",
                    body=(
                        f"Adopt a {provider} landing zone with isolated environments, managed database services, "
                        "object storage for file exports, and approval-gated delivery controls."
                    ),
                    citations=top_evidence[:2],
                ),
            ],
        ),
        Report(
            id="report-wave-plan",
            kind="migration_wave_plan",
            title="Migration Wave Plan",
            summary="Remediation, platform foundation, and controlled cutover waves derived from the current blocker set.",
            confidence=max(0.76, overview.confidence - 0.04),
            generated_at=generated_at,
            artifact_ids=[artifact_map["migration_wave_plan"]],
            sections=[
                ReportSection(
                    title="Wave 0 - Remediation",
                    body="Close secrets, logging, and transport blockers before enabling planning-sensitive write paths.",
                    citations=top_evidence[:2],
                ),
                ReportSection(
                    title="Wave 1 - Foundation",
                    body="Stand up the landing zone, managed database target, object storage flows, and observability baseline.",
                    citations=top_evidence[1:3],
                ),
                ReportSection(
                    title="Wave 2 - Cutover",
                    body="Run restore tests, replay critical jobs, and execute cutover only with explicit approval and rollback readiness.",
                    citations=top_evidence[:2],
                ),
            ],
        ),
        Report(
            id="report-cutover-rollback",
            kind="cutover_rollback",
            title="Cutover and Rollback Plan",
            summary="Rollback-aware migration guidance with data protection, restore testing, and reversible traffic movement.",
            confidence=max(0.74, overview.confidence - 0.05),
            generated_at=generated_at,
            artifact_ids=[artifact_map["cutover_rollback"]],
            sections=[
                ReportSection(
                    title="Cutover Controls",
                    body="Freeze risky configuration changes, validate restore points, and confirm critical job paths before traffic movement.",
                    citations=top_evidence[:2],
                ),
                ReportSection(
                    title="Rollback Controls",
                    body="Keep source workloads reversible during the validation window and define trigger thresholds for rollback before cutover begins.",
                    citations=top_evidence[1:3],
                ),
            ],
        ),
        Report(
            id="report-ops-checklist",
            kind="operations_checklist",
            title="Operations and Monitoring Checklist",
            summary="Operations readiness checklist for observability, ownership, backup, DR, and approval discipline.",
            confidence=max(0.73, overview.confidence - 0.06),
            generated_at=generated_at,
            artifact_ids=[artifact_map["operations_checklist"]],
            sections=[
                ReportSection(
                    title="Checklist",
                    body=(
                        "Define SLO baselines, on-call ownership, log retention controls, backup verification, "
                        "RPO/RTO targets, restore drills, and approval workflows before execution is enabled."
                    ),
                    citations=[
                        evidence_by_id[item.id]
                        for item in top_evidence[:2]
                        if item.id in evidence_by_id
                    ],
                ),
            ],
        ),
    ]


def _build_approvals() -> list[ApprovalRecord]:
    return [
        ApprovalRecord(
            id="approval-assessment-closeout",
            phase="Assessment Signoff",
            state="approved",
            requested_by="Ava Patel",
            approver="Marcus Lim",
            comment="Assessment findings are accepted and planning may begin once blockers are tracked.",
            decided_at=datetime.now(UTC).replace(microsecond=0),
        ),
        ApprovalRecord(
            id="approval-planning",
            phase="Planning Phase",
            state="pending",
            requested_by="Ava Patel",
        ),
        ApprovalRecord(
            id="approval-execution",
            phase="Execution Phase",
            state="not_required",
            requested_by="system",
        ),
    ]


def _build_audit_events(scan, generated_at: datetime) -> list[AuditEvent]:
    return [
        AuditEvent(
            id="audit-scan-started",
            actor="local-worker",
            action="scan.started",
            entity_type="migration_project",
            entity_id=scan.project_id or "legacycart",
            created_at=generated_at,
            metadata={"source": "demo-systems/legacycart", "mode": "read_only"},
        ),
        AuditEvent(
            id="audit-scan-completed",
            actor="local-worker",
            action="scan.completed",
            entity_type="migration_project",
            entity_id=scan.project_id or "legacycart",
            created_at=generated_at,
            metadata={
                "evidenceItems": str(len(scan.evidence)),
                "findings": str(len(scan.findings)),
                "recommendation": str(scan.summary.recommendation),
            },
        ),
        AuditEvent(
            id="audit-reports-prepared",
            actor="reporting-engine",
            action="report.prepared",
            entity_type="migration_project",
            entity_id=scan.project_id or "legacycart",
            created_at=generated_at,
            metadata={"reports": "8", "exports": "available"},
        ),
    ]


def _build_chat_messages(
    generated_at: datetime,
    overview: ProjectOverview,
    findings: list[Finding],
) -> list[ChatMessage]:
    lead_finding = findings[0]
    return [
        ChatMessage(
            id="chat-001",
            author="Taylor Reed",
            role="human",
            created_at=generated_at,
            content="Can we move into planning while keeping execution disabled?",
        ),
        ChatMessage(
            id="chat-002",
            author="Cockpit Assistant",
            role="ai",
            created_at=generated_at,
            content=(
                f"Yes. Planning can proceed while execution remains approval-gated, but the top blocker is "
                f"'{lead_finding.title}'. The current recommendation is {overview.migration_decision.lower()}."
            ),
        ),
    ]
