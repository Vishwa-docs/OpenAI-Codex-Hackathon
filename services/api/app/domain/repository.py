from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from re import sub

from ..core.db import ProjectSnapshotRecord, session_scope
from ..core.settings import get_settings
from .models import (
    AnalysisQuestion,
    AssessmentRun,
    ClientAccountSummary,
    DeploymentArtifact,
    DeploymentExecution,
    DeploymentPlan,
    ChatMessage,
    CloudConnection,
    ApprovalRecord,
    ArtifactFormat,
    AuditEvent,
    CredentialRef,
    FactoryProposal,
    DependencyEdge,
    DependencyGraph,
    DependencyNode,
    EvidenceLocator,
    EvidenceReference,
    Finding,
    IntakeProfile,
    ObservabilityTrace,
    PlatformRecommendation,
    OrganizationSummary,
    ProjectOverview,
    ProjectCreate,
    ProjectSeed,
    PreviewDeploymentStatus,
    RuntimeDescriptor,
    SourceConnection,
    RegistryEntry,
    Report,
    ReportArtifact,
    ReportSection,
    SourceConnectionCreate,
    CloudConnectionCreate,
    ChatMessageCreate,
    WorkspaceContext,
    WorkspaceSummary,
    normalize_source_kind,
)
from services.worker.app.scanner import scan_legacycart


class SeedRepository:
    """In-memory repository with a deterministic seeded legacy migration project."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._projects = self._load_projects()

    def _load_projects(self) -> dict[str, ProjectSeed]:
        with session_scope() as session:
            records = session.query(ProjectSnapshotRecord).all()
            if records:
                return {
                    record.project_id: ProjectSeed.model_validate(json.loads(record.payload_json))
                    for record in records
                }

            if self.settings.should_seed_demo_data:
                seed = self._build_legacycart()
                session.merge(
                    ProjectSnapshotRecord(
                        project_id=seed.overview.id,
                        payload_json=seed.model_dump_json(by_alias=True),
                    )
                )
                return {seed.overview.id: seed}

            return {}

    def _save_project(self, project: ProjectSeed) -> None:
        with session_scope() as session:
            session.merge(
                ProjectSnapshotRecord(
                    project_id=project.overview.id,
                    payload_json=project.model_dump_json(by_alias=True),
                )
            )

    def save_project(self, project: ProjectSeed) -> None:
        self._projects[project.overview.id] = project
        self._save_project(project)

    def get_project(self, project_id: str) -> ProjectSeed:
        if project_id not in self._projects:
            raise KeyError(project_id)
        return self._projects[project_id]

    def list_projects(self) -> list[ProjectOverview]:
        return [project.overview for project in self._projects.values()]

    def get_workspace_context(self, workspace_id: str) -> WorkspaceContext:
        if workspace_id != self.settings.default_workspace_id:
            raise KeyError(workspace_id)
        projects = self.list_projects()
        legacy_project = self._projects.get("legacycart")
        client_accounts = (
            [
                ClientAccountSummary(
                    id="client-demo-northstar",
                    workspace_id=self.settings.default_workspace_id,
                    name=legacy_project.overview.client_name,
                    industry="Retail",
                    primary_region="us-east-1",
                    compliance_tags=["PCI-lite", "Customer PII"],
                )
            ]
            if legacy_project is not None and self.settings.is_demo_mode
            else []
        )
        return WorkspaceContext(
            organization=OrganizationSummary(
                id=self.settings.default_organization_id,
                name="Cloud Migration Cockpit Judge Org" if self.settings.is_judge_mode else "Cloud Migration Cockpit Demo Org",
                slug="judge-org" if self.settings.is_judge_mode else "demo-org",
                mode="judge" if self.settings.is_judge_mode else "demo",
            ),
            workspace=WorkspaceSummary(
                id=self.settings.default_workspace_id,
                organization_id=self.settings.default_organization_id,
                name="Judge Workspace" if self.settings.is_judge_mode else "Demo Workspace",
                slug="judge-workspace" if self.settings.is_judge_mode else "demo-workspace",
                mode="judge" if self.settings.is_judge_mode else "demo",
                project_count=len(projects),
            ),
            client_accounts=client_accounts,
            projects=projects,
            runtime=RuntimeDescriptor(
                app_mode="judge" if self.settings.is_judge_mode else "demo",
                default_workspace_id=self.settings.default_workspace_id,
                desktop_download_url=self.settings.desktop_download_url,
                desktop_available=self.settings.desktop_build_path.exists(),
                version="0.1.0",
            ),
        )

    def list_workspace_projects(self, workspace_id: str) -> list[ProjectOverview]:
        return self.get_workspace_context(workspace_id).projects

    def create_workspace_project(self, workspace_id: str, draft: ProjectCreate) -> ProjectOverview:
        if workspace_id != self.settings.default_workspace_id:
            raise KeyError(workspace_id)
        if draft.source_kind and draft.source_target:
            return self.create_project(draft).overview
        project_id = sub(r"[^a-z0-9]+", "-", draft.name.lower()).strip("-") or f"project-{len(self._projects) + 1}"
        if project_id in self._projects:
            project_id = f"{project_id}-{len(self._projects) + 1}"
        now = datetime(2026, 4, 16, 12, 10, tzinfo=UTC)
        overview = ProjectOverview(
            id=project_id,
            name=draft.name,
            client_name=draft.client_name,
            readiness_score=0,
            migration_decision="Intake in progress",
            confidence=0.0,
            phase="Intake",
            status="Draft intake",
            recommended_provider="Pending",
        )
        project = ProjectSeed(
            overview=overview,
            evidence=[],
            findings=[],
            graph=DependencyGraph(nodes=[], edges=[], generated_at=now, summary="No source evidence has been ingested yet."),
            source_connections=[],
            cloud_connections=[],
            factory_proposals=[],
            chat_messages=[
                ChatMessage(
                    id=f"{project_id}-chat-001",
                    role="system",
                    author="Cloud Migration Cockpit",
                    created_at=now,
                    content="Project created. Complete intake, connect a source, and run the first assessment.",
                )
            ],
            approvals=[
                ApprovalRecord(id=f"{project_id}-approval-planning", phase="Planning Phase", state="pending", requested_by=draft.owner or "system"),
                ApprovalRecord(id=f"{project_id}-approval-execution", phase="Execution Phase", state="not_required", requested_by="system"),
            ],
            audit_events=[
                AuditEvent(
                    id=f"{project_id}-audit-created",
                    actor=draft.owner or "system",
                    action="project.created",
                    entity_type="migration_project",
                    entity_id=project_id,
                    created_at=now,
                    metadata={"workspaceId": workspace_id, "mode": self.settings.app_mode},
                )
            ],
            registry_entries=[],
            reports=[],
            artifacts=[],
            intake_profile=None,
            deployment_plan=None,
            observability_traces=[],
            deployment_executions=[],
        )
        self._projects[project_id] = project
        self._save_project(project)
        return overview

    def create_project(self, draft: ProjectCreate) -> ProjectSeed:
        slug = sub(r"[^a-z0-9]+", "-", draft.name.lower()).strip("-") or f"project-{len(self._projects) + 1}"
        project_id = slug if slug not in self._projects else f"{slug}-{len(self._projects) + 1}"
        now = datetime(2026, 4, 16, 12, 0, tzinfo=UTC)
        source_kind = normalize_source_kind(draft.source_kind or "local_path")
        source_target = draft.source_target or ""
        expected_users = draft.expected_users or 25
        credential_kind = draft.credential_kind or "none"
        credential_label = draft.credential_label or ("Local path" if source_kind == "local_path" else "Source credential")

        try:
            scan_result = (
                scan_legacycart(Path(source_target))
                if source_kind == "local_path" and source_target and Path(source_target).exists()
                else None
            )
        except Exception:
            scan_result = None

        founder_summary = (
            f"This project is being assessed for about {expected_users} users. "
            "The cockpit will favor simpler hosting first and only suggest heavier cloud patterns when the code or traffic justifies it."
        )

        if scan_result is not None:
            project = self._build_project_from_scan(
                project_id=project_id,
                draft=draft,
                source_kind=source_kind,
                source_target=source_target,
                credential_kind=credential_kind,
                credential_label=credential_label,
                founder_summary=founder_summary,
                now=now,
                scan_result=scan_result,
            )
            self._projects[project_id] = project
            self._save_project(project)
            return project

        if self.settings.should_seed_demo_data and "legacycart" in self._projects:
            base = self.get_project("legacycart").model_copy(deep=True)
        else:
            base = self._build_empty_project_seed(project_id, draft, founder_summary, now)

        base.overview = base.overview.model_copy(
            update={
                "id": project_id,
                "name": draft.name,
                "client_name": draft.client_name,
                "readiness_score": min(80, max(35, 72 - expected_users // 12)),
                "migration_decision": "Assessing real codebase and migration options",
                "phase": "intake",
                "status": "intake_ready",
                "recommended_provider": draft.preferred_cloud.upper(),
            }
        )
        base.source_connections = [
            SourceConnection(
                id=f"{project_id}-source-1",
                kind=source_kind,
                name="Primary source",
                status="connected" if source_kind == "local_path" else "needs_attention",
                mode="discovery" if source_kind != "local_path" else "read_only",
                target=source_target,
                branch="main" if source_kind != "local_path" else None,
                last_sync_at=now if source_kind == "local_path" else None,
                credential_ref=CredentialRef(
                    id=f"{project_id}-source-cred",
                    kind=credential_kind,
                    label=credential_label,
                    redacted_value=f"{credential_kind}_****",
                ),
                notes=[
                    "Created from the desktop intake wizard.",
                    "The system should keep discovery read-only until planning is reviewed.",
                ],
            )
        ]
        base.cloud_connections = []
        base.chat_messages = [
            ChatMessage(
                id=f"{project_id}-chat-001",
                author="Cockpit Assistant",
                role="ai",
                created_at=now,
                content=founder_summary,
            )
        ]
        base.approvals = [
            ApprovalRecord(id=f"{project_id}-approval-assessment", phase="Assessment Signoff", state="approved", requested_by="system", approver="system", comment="Initial intake accepted.", decided_at=now),
            ApprovalRecord(id=f"{project_id}-approval-planning", phase="Planning Phase", state="pending", requested_by="system"),
            ApprovalRecord(id=f"{project_id}-approval-execution", phase="Execution Phase", state="not_required", requested_by="system"),
        ]
        base.audit_events = [
            AuditEvent(
                id=f"{project_id}-audit-intake",
                actor="desktop-intake",
                action="project.created",
                entity_type="migration_project",
                entity_id=project_id,
                created_at=now,
                metadata={"sourceKind": draft.source_kind, "expectedUsers": str(draft.expected_users)},
            )
        ]
        base.registry_entries = base.registry_entries + [
            RegistryEntry(
                id=f"{project_id}-reg-terraform",
                name="Terraform Planning Adapter",
                kind="tool",
                status="enabled",
                required_permissions=["plan:terraform"],
                rationale="Generates an approval-gated Terraform starter for the recommended AWS path.",
                version="1.0.0",
                proposed_by="MTC Swarm",
                enabled=True,
            ),
            RegistryEntry(
                id=f"{project_id}-reg-ansible",
                name="Ansible Bootstrap Adapter",
                kind="tool",
                status="enabled",
                required_permissions=["plan:ansible"],
                rationale="Generates bootstrap automation when VM-first or EC2-first paths are more appropriate than containers.",
                version="1.0.0",
                proposed_by="MTC Swarm",
                enabled=True,
            ),
        ]
        base.intake_profile = IntakeProfile(
            id=project_id,
            project_id=project_id,
            name=draft.name,
            client_name=draft.client_name,
            source_kind=source_kind,
            source_target=source_target,
            expected_users=expected_users,
            preferred_cloud=draft.preferred_cloud,
            business_constraints=draft.business_constraints,
            compliance_notes=draft.compliance_notes,
            credential_label=credential_label,
            credential_kind=credential_kind,
            founder_summary=founder_summary,
        )
        base.deployment_plan = self._build_deployment_plan(project_id, expected_users, source_kind, False)
        base.observability_traces = self._build_observability_traces(project_id)
        base.deployment_executions = []
        base.analysis_questions = []
        base.preview_status = self._build_preview_status(source_target, now)
        self._projects[project_id] = base
        self._save_project(base)
        return base

    def _build_empty_project_seed(
        self,
        project_id: str,
        draft: ProjectCreate,
        founder_summary: str,
        now: datetime,
    ) -> ProjectSeed:
        return ProjectSeed(
            overview=ProjectOverview(
                id=project_id,
                name=draft.name,
                client_name=draft.client_name,
                readiness_score=0,
                migration_decision="Intake in progress",
                confidence=0.0,
                phase="Intake",
                status="Draft intake",
                recommended_provider="Pending",
            ),
            evidence=[],
            findings=[],
            graph=DependencyGraph(nodes=[], edges=[], generated_at=now, summary="No source evidence has been ingested yet."),
            source_connections=[],
            cloud_connections=[],
            factory_proposals=[],
            chat_messages=[
                ChatMessage(
                    id=f"{project_id}-chat-001",
                    role="system",
                    author="Cloud Migration Cockpit",
                    created_at=now,
                    content=founder_summary,
                )
            ],
            approvals=[
                ApprovalRecord(id=f"{project_id}-approval-planning", phase="Planning Phase", state="pending", requested_by=draft.owner or "system"),
                ApprovalRecord(id=f"{project_id}-approval-execution", phase="Execution Phase", state="not_required", requested_by="system"),
            ],
            audit_events=[
                AuditEvent(
                    id=f"{project_id}-audit-created",
                    actor=draft.owner or "system",
                    action="project.created",
                    entity_type="migration_project",
                    entity_id=project_id,
                    created_at=now,
                    metadata={"workspaceId": self.settings.default_workspace_id, "mode": self.settings.app_mode},
                )
            ],
            registry_entries=[],
            reports=[],
            artifacts=[],
            intake_profile=None,
            deployment_plan=None,
            observability_traces=[],
            deployment_executions=[],
            analysis_questions=[],
            preview_status=self._build_preview_status(draft.source_target, now),
        )

    def _build_project_from_scan(
        self,
        *,
        project_id: str,
        draft: ProjectCreate,
        source_kind: str,
        source_target: str,
        credential_kind: str,
        credential_label: str,
        founder_summary: str,
        now: datetime,
        scan_result,
    ) -> ProjectSeed:
        evidence_by_id = {
            item.id: EvidenceReference(
                id=item.id,
                source_type=item.source_type,
                source_uri=item.source_uri,
                excerpt=item.excerpt,
                locator=(
                    EvidenceLocator(
                        line_start=item.locator.get("lineStart"),
                        line_end=item.locator.get("lineEnd"),
                    )
                    if item.locator
                    else None
                ),
                confidence=item.confidence,
            )
            for item in scan_result.evidence
        }
        findings = [
            Finding(
                id=item.id,
                title=item.title,
                category=item.category,
                severity=item.severity,
                confidence=item.confidence,
                summary=item.summary,
                recommendation=item.recommendation,
                evidence=[evidence_by_id[evidence_id] for evidence_id in item.evidence_ids if evidence_id in evidence_by_id],
            )
            for item in scan_result.findings
        ]
        nodes = []
        for index, component in enumerate(scan_result.components):
            kind = component.kind
            if kind == "integration":
                graph_kind = "external_api"
            elif kind == "frontend":
                graph_kind = "service"
            else:
                graph_kind = kind
            nodes.append(
                DependencyNode(
                    id=component.id,
                    label=component.name,
                    kind=graph_kind,
                    environment="legacy",
                    status="observed",
                    x=180 + (index % 3) * 220,
                    y=160 + (index // 3) * 180,
                )
            )
        edges = [
            DependencyEdge(
                id=item.id,
                source=item.source,
                target=item.target,
                relation=item.relation,
            )
            for item in scan_result.dependencies
        ]
        preview_status = self._build_preview_status(source_target, now)
        analysis_questions = self._build_analysis_questions(project_id, findings, now)
        recommended_provider = scan_result.summary.provider_ranking[0]["provider"] if scan_result.summary.provider_ranking else draft.preferred_cloud.upper()
        return ProjectSeed(
            overview=ProjectOverview(
                id=project_id,
                name=draft.name,
                client_name=draft.client_name,
                readiness_score=scan_result.summary.readiness_score,
                migration_decision=scan_result.summary.recommendation.title(),
                confidence=scan_result.summary.confidence,
                phase="analysis",
                status="questions_pending" if analysis_questions else "analysis_ready",
                recommended_provider=str(recommended_provider),
            ),
            evidence=list(evidence_by_id.values()),
            findings=findings,
            graph=DependencyGraph(
                nodes=nodes,
                edges=edges,
                generated_at=now,
                summary=f"Dependency graph built from {scan_result.root_path}.",
            ),
            source_connections=[
                SourceConnection(
                    id=f"{project_id}-source-1",
                    kind=source_kind,
                    name="Primary source",
                    status="connected",
                    mode="read_only",
                    target=source_target,
                    last_sync_at=now,
                    credential_ref=CredentialRef(
                        id=f"{project_id}-source-cred",
                        kind=credential_kind,
                        label=credential_label,
                        redacted_value=f"{credential_kind}_****",
                    ),
                    notes=["Scanned from a real local path in judge mode."],
                )
            ],
            cloud_connections=[],
            factory_proposals=[],
            chat_messages=[
                ChatMessage(
                    id=f"{project_id}-chat-001",
                    role="system",
                    author="Cloud Migration Cockpit",
                    created_at=now,
                    content=founder_summary,
                )
            ],
            approvals=[
                ApprovalRecord(id=f"{project_id}-approval-planning", phase="Planning Phase", state="pending", requested_by="system"),
                ApprovalRecord(id=f"{project_id}-approval-execution", phase="Execution Phase", state="not_required", requested_by="system"),
            ],
            audit_events=[
                AuditEvent(
                    id=f"{project_id}-audit-created",
                    actor="desktop-intake",
                    action="project.created",
                    entity_type="migration_project",
                    entity_id=project_id,
                    created_at=now,
                    metadata={"sourceKind": source_kind, "workspaceId": self.settings.default_workspace_id},
                ),
                AuditEvent(
                    id=f"{project_id}-audit-scan",
                    actor="local-worker",
                    action="source.scanned",
                    entity_type="source_connection",
                    entity_id=f"{project_id}-source-1",
                    created_at=now,
                    metadata={"sourceTarget": source_target, "evidenceCount": str(len(evidence_by_id))},
                ),
            ],
            registry_entries=[],
            reports=[],
            artifacts=[],
            intake_profile=IntakeProfile(
                id=project_id,
                project_id=project_id,
                name=draft.name,
                client_name=draft.client_name,
                source_kind=source_kind,
                source_target=source_target,
                expected_users=draft.expected_users or 25,
                preferred_cloud=draft.preferred_cloud,
                business_constraints=draft.business_constraints,
                compliance_notes=draft.compliance_notes,
                credential_label=credential_label,
                credential_kind=credential_kind,
                founder_summary=founder_summary,
            ),
            deployment_plan=self._build_deployment_plan(project_id, draft.expected_users or 25, source_kind, False),
            observability_traces=self._build_observability_traces(project_id),
            deployment_executions=[],
            analysis_questions=analysis_questions,
            preview_status=preview_status,
        )

    def _build_analysis_questions(
        self,
        project_id: str,
        findings: list[Finding],
        now: datetime,  # noqa: ARG002 - keeps call sites timestamp-ready for persisted follow-ups
    ) -> list[AnalysisQuestion]:
        questions: list[AnalysisQuestion] = []
        if any(finding.category in {"secrets", "security", "logging"} for finding in findings):
            questions.append(
                AnalysisQuestion(
                    id=f"{project_id}-question-security",
                    stage="security_readiness",
                    question="Which secrets manager and log retention policy should the migration target use?",
                    rationale="The scan found credential or sensitive logging issues that must be closed before execution.",
                )
            )
        if any(finding.category in {"integration", "operations", "delivery"} for finding in findings):
            questions.append(
                AnalysisQuestion(
                    id=f"{project_id}-question-cutover",
                    stage="migration_strategy",
                    question="Which external integrations and batch jobs must remain unchanged in the first migration wave?",
                    rationale="The scan found coupled jobs or external dependencies that influence the safest first wave.",
                )
            )
        return questions

    @staticmethod
    def _build_preview_status(source_target: str | None, now: datetime) -> PreviewDeploymentStatus:
        root = Path(source_target) if source_target else None
        supported = bool(root and root.exists() and ((root / "package.json").exists() or (root / "pnpm-workspace.yaml").exists()))
        if supported:
            return PreviewDeploymentStatus(
                status="ready",
                supported=True,
                summary="A Node-based local preview can be launched from the working copy after planning approval.",
                workspace_path=str(root),
                updated_at=now,
            )
        return PreviewDeploymentStatus(
            status="unsupported",
            supported=False,
            summary="Local preview automation is currently limited to Node-based web app monorepos.",
            workspace_path=str(root) if root else None,
            updated_at=now,
        )

    def get_intake_profile(self, project_id: str) -> IntakeProfile:
        project = self.get_project(project_id)
        if project.intake_profile is None:
            raise KeyError(project_id)
        return project.intake_profile

    def get_deployment_plan(self, project_id: str) -> DeploymentPlan:
        project = self.get_project(project_id)
        if project.deployment_plan is None:
            has_aws = any(item.provider == "aws" for item in project.cloud_connections)
            expected_users = project.intake_profile.expected_users if project.intake_profile else 250
            project.deployment_plan = self._build_deployment_plan(project_id, expected_users, project.intake_profile.source_kind if project.intake_profile else "local_path", has_aws)
        return project.deployment_plan

    def list_observability_traces(self, project_id: str) -> list[ObservabilityTrace]:
        return self.get_project(project_id).observability_traces

    def add_source_connection(self, project_id: str, draft: SourceConnectionCreate) -> SourceConnection:
        project = self.get_project(project_id)
        connection = SourceConnection(
            id=f"source-{draft.kind}-{len(project.source_connections) + 1}",
            kind=draft.kind,
            name=draft.name,
            status="needs_configuration",
            mode=draft.mode,
            target=draft.target,
            branch=draft.branch,
            last_sync_at=datetime(2026, 4, 16, 11, 0, tzinfo=UTC),
            credential_ref=CredentialRef(
                id=f"cred-{draft.kind}-{len(project.source_connections) + 1}",
                kind=draft.credential_kind,
                label=draft.credential_label,
                redacted_value=f"{draft.credential_kind}_****",
            ),
            notes=draft.notes,
        )
        project.source_connections.append(connection)
        project.audit_events.append(
            AuditEvent(
                id=f"audit-source-{len(project.audit_events) + 1}",
                actor="control-plane",
                action="source_connection.created",
                entity_type="source_connection",
                entity_id=connection.id,
                created_at=datetime(2026, 4, 16, 11, 0, 5, tzinfo=UTC),
                metadata={"kind": draft.kind, "target": draft.target},
            )
        )
        self._save_project(project)
        return connection

    def add_cloud_connection(self, project_id: str, draft: CloudConnectionCreate) -> CloudConnection:
        project = self.get_project(project_id)
        connection = CloudConnection(
            id=f"cloud-{draft.provider}-{len(project.cloud_connections) + 1}",
            provider=draft.provider,
            name=draft.name,
            status="needs_configuration",
            mode=draft.mode,
            account_label=draft.account_label,
            region_scope=draft.region_scope,
            credential_ref=CredentialRef(
                id=f"cred-{draft.provider}-{len(project.cloud_connections) + 1}",
                kind=draft.credential_kind,
                label=draft.credential_label,
                redacted_value=f"{draft.provider}_****",
            ),
            notes=draft.notes,
        )
        project.cloud_connections.append(connection)
        project.audit_events.append(
            AuditEvent(
                id=f"audit-cloud-{len(project.audit_events) + 1}",
                actor="control-plane",
                action="cloud_connection.created",
                entity_type="cloud_connection",
                entity_id=connection.id,
                created_at=datetime(2026, 4, 16, 11, 1, tzinfo=UTC),
                metadata={"provider": draft.provider, "accountLabel": draft.account_label},
            )
        )
        if draft.provider == "aws" and project.deployment_plan is not None:
            project.deployment_plan = self._build_deployment_plan(
                project_id,
                project.intake_profile.expected_users if project.intake_profile else 250,
                project.intake_profile.source_kind if project.intake_profile else "local_path",
                True,
            )
        self._save_project(project)
        return connection

    def add_chat_message(self, project_id: str, draft: ChatMessageCreate) -> ChatMessage:
        project = self.get_project(project_id)
        message = ChatMessage(
            id=f"chat-{len(project.chat_messages) + 1:03d}",
            role=draft.role,
            author=draft.author,
            created_at=datetime(2026, 4, 16, 11, 2, tzinfo=UTC),
            content=draft.content,
        )
        project.chat_messages.append(message)
        project.audit_events.append(
            AuditEvent(
                id=f"audit-chat-{len(project.audit_events) + 1}",
                actor=draft.author,
                action="chat.message_created",
                entity_type="chat_message",
                entity_id=message.id,
                created_at=datetime(2026, 4, 16, 11, 2, 5, tzinfo=UTC),
                metadata={"role": draft.role},
            )
        )
        self._save_project(project)
        return message

    def add_assessment_run(self, project_id: str, run: AssessmentRun, triggered_by: str) -> AssessmentRun:
        project = self.get_project(project_id)
        project.assessment_runs.insert(0, run)
        project.audit_events.append(
            AuditEvent(
                id=f"audit-assessment-{len(project.audit_events) + 1}",
                actor=triggered_by,
                action="assessment.requested",
                entity_type="assessment_run",
                entity_id=run.id,
                created_at=datetime(2026, 4, 16, 11, 3, tzinfo=UTC),
                metadata={"mode": run.mode},
            )
        )
        self._save_project(project)
        return run

    def add_deployment_execution(
        self,
        project_id: str,
        provider: str,
        mode: str,
        triggered_by: str,
    ) -> DeploymentExecution:
        project = self.get_project(project_id)
        execution = DeploymentExecution(
            id=f"{project_id}-deploy-{len(project.deployment_executions) + 1:03d}",
            provider="aws",
            mode=mode,  # type: ignore[arg-type]
            status="succeeded",
            triggered_by=triggered_by,
            summary="AWS deployment adapter completed the requested demo execution path.",
            created_at=datetime(2026, 4, 16, 12, 5, tzinfo=UTC),
            next_steps=[
                "Review generated Terraform and Ansible artifacts.",
                "Confirm security findings are accepted before a real apply.",
            ],
        )
        project.deployment_executions.insert(0, execution)
        project.deployment_plan = self._build_deployment_plan(
            project_id,
            project.intake_profile.expected_users if project.intake_profile else 250,
            project.intake_profile.source_kind if project.intake_profile else "local_path",
            True,
            last_execution=execution,
        )
        self._save_project(project)
        return execution

    @staticmethod
    def _build_deployment_plan(
        project_id: str,
        expected_users: int,
        source_kind: str,
        has_aws_credentials: bool,
        *,
        last_execution: DeploymentExecution | None = None,
    ) -> DeploymentPlan:
        platform_options = [
            PlatformRecommendation(
                platform_key="vercel",
                label="Vercel",
                fit_score=95 if source_kind == "github" and expected_users <= 50 else 60 if expected_users <= 50 else 54,
                best_for="Frontend-heavy products and low-ops launches.",
                rationale="Excellent for static or mostly frontend apps when speed matters more than deep infrastructure control.",
                plain_language_rationale="Great when the app is mostly a website and you want to go live quickly without a lot of DevOps overhead.",
                tradeoffs=["Limited fit for heavy background jobs", "Backend complexity may outgrow it"],
                monthly_cost_estimate="$20-$150",
                scaling_threshold="Best under roughly 50-100 active users at this stage",
                execution_ready=False,
            ),
            PlatformRecommendation(
                platform_key="railway",
                label="Railway",
                fit_score=90 if source_kind == "github" and expected_users <= 120 else 72 if expected_users <= 120 else 63,
                best_for="Simple full-stack apps and small teams.",
                rationale="Useful for lean teams that need a quick deploy for a simple backend without building a full platform team.",
                plain_language_rationale="Good when you have a simple app and want a little more backend flexibility than a static host.",
                tradeoffs=["Less control than AWS", "Can become expensive at higher scale"],
                monthly_cost_estimate="$20-$250",
                scaling_threshold="Best under roughly 100-200 active users",
                execution_ready=False,
            ),
            PlatformRecommendation(
                platform_key="aws-ec2",
                label="AWS EC2",
                fit_score=92 if source_kind == "local_path" and expected_users <= 500 else 78 if expected_users <= 500 else 76,
                best_for="Simple backends, early production hardening, and teams that want AWS control without microservices.",
                rationale="Strong bridge option between a vibe-coded prototype and a production-ready AWS footprint.",
                plain_language_rationale="A simple server on AWS is often the right first production step when managed microservices would be overkill.",
                tradeoffs=["You manage more ops yourself", "Needs patching and monitoring discipline"],
                monthly_cost_estimate="$40-$300",
                scaling_threshold="Strong first AWS step up to a few hundred users",
                execution_ready=has_aws_credentials,
            ),
            PlatformRecommendation(
                platform_key="aws-ecs",
                label="AWS ECS / Fargate",
                fit_score=78 if expected_users > 200 else 61,
                best_for="Containerized apps and steady growth.",
                rationale="A better fit once the app has clearer service boundaries and container packaging.",
                plain_language_rationale="Useful once the app is growing and you need more automation, but it is more setup than a single server.",
                tradeoffs=["More moving pieces", "Higher platform complexity"],
                monthly_cost_estimate="$120-$700",
                scaling_threshold="Best when growth and ops maturity justify container orchestration",
                execution_ready=has_aws_credentials,
            ),
            PlatformRecommendation(
                platform_key="aws-lambda",
                label="AWS Lambda",
                fit_score=70 if expected_users <= 100 else 58,
                best_for="Event-driven APIs and small functions.",
                rationale="Good for isolated tasks, but not every app should be forced into serverless shapes.",
                plain_language_rationale="Helpful for small background tasks or APIs, but not always the simplest path for a whole app.",
                tradeoffs=["Cold starts and service limits", "Requires code to fit serverless constraints"],
                monthly_cost_estimate="$5-$200",
                scaling_threshold="Best for event-driven features rather than monolith-first migrations",
                execution_ready=has_aws_credentials,
            ),
            PlatformRecommendation(
                platform_key="cloudflare-workers",
                label="Cloudflare Workers",
                fit_score=74 if expected_users <= 80 else 49,
                best_for="Edge APIs and lightweight request handling.",
                rationale="Interesting for latency-sensitive or frontend-adjacent workloads, but not a universal migration answer.",
                plain_language_rationale="Fast at the edge, but only if the app is lightweight enough to fit that model.",
                tradeoffs=["Runtime constraints", "Not ideal for traditional server apps"],
                monthly_cost_estimate="$5-$100",
                scaling_threshold="Best for lightweight request paths and edge logic",
                execution_ready=False,
            ),
        ]
        ranked = sorted(platform_options, key=lambda option: option.fit_score, reverse=True)
        if source_kind == "github" and expected_users <= 50:
            recommended = next(option for option in ranked if option.platform_key == "vercel")
        elif expected_users <= 500:
            recommended = next(option for option in ranked if option.platform_key == "aws-ec2")
        else:
            recommended = next(option for option in ranked if option.platform_key == "aws-ecs")
        founder_summary = (
            f"In plain language: for about {expected_users} users, you probably do not need complex microservices on day one. "
            f"The best starting option here is {recommended.label}, because it keeps the system simpler while still leaving room to grow."
        )
        execution_state = "succeeded" if last_execution else "ready" if has_aws_credentials else "blocked"
        return DeploymentPlan(
            project_id=project_id,
            execution_state=execution_state,
            founder_summary=founder_summary,
            recommended_platform=recommended,
            platform_options=ranked,
            required_actions=(
                []
                if has_aws_credentials
                else [
                    "Connect an AWS credential or assumed role in the cockpit.",
                    "Review Terraform and Ansible previews before enabling execution.",
                    "Approve the planning phase before apply mode.",
                ]
            ),
            artifacts=[
                DeploymentArtifact(
                    id=f"{project_id}-tf-plan",
                    kind="terraform",
                    title="AWS landing zone Terraform starter",
                    summary="Creates networking, compute, storage, and security scaffolding for the recommended AWS path.",
                    preview='module "app_host" { source = "./modules/ec2_or_app" }',
                ),
                DeploymentArtifact(
                    id=f"{project_id}-ansible-bootstrap",
                    kind="ansible",
                    title="Bootstrap playbook",
                    summary="Configures runtime packages, app bootstrap, and observability agents for VM-first paths.",
                    preview="- hosts: app\n  tasks:\n    - name: Install runtime packages",
                ),
                DeploymentArtifact(
                    id=f"{project_id}-deploy-checklist",
                    kind="checklist",
                    title="Deployment checklist",
                    summary="Human-readable checklist that keeps the deployment reviewable for non-technical founders.",
                    preview="1. Confirm expected users.\n2. Review costs.\n3. Approve AWS dry run.",
                ),
            ],
            last_execution=last_execution,
        )

    @staticmethod
    def _build_observability_traces(project_id: str) -> list[ObservabilityTrace]:
        return [
            ObservabilityTrace(
                id=f"{project_id}-trace-001",
                stage_key="intake_clarification",
                agent_key="founder_intake_guide",
                title="Founder Intake Guide",
                status="succeeded",
                summary="Captured business context, expected users, and complexity guardrails.",
                confidence=0.93,
                latency_ms=180,
                evidence_count=2,
                evaluation_summary="Questions were complete enough to choose between simple hosting and heavier cloud paths.",
                question_checkpoint="How many users are expected in the first production phase?",
            ),
            ObservabilityTrace(
                id=f"{project_id}-trace-002",
                stage_key="codebase_discovery",
                agent_key="codebase_discovery",
                title="Codebase Discovery",
                status="succeeded",
                summary="Scanned the supplied source and extracted components, dependencies, and risk hints.",
                confidence=0.9,
                latency_ms=420,
                evidence_count=6,
                evaluation_summary="Discovery remained read-only and evidence-backed.",
            ),
            ObservabilityTrace(
                id=f"{project_id}-trace-003",
                stage_key="hosting_fit_recommendation",
                agent_key="hosting_fit_advisor",
                title="Hosting Fit Advisor",
                status="succeeded",
                summary="Ranked simpler and heavier deployment targets instead of defaulting to microservices.",
                confidence=0.88,
                latency_ms=240,
                evidence_count=4,
                warnings=["Managed microservices were intentionally deprioritized for lower expected traffic."],
                evaluation_summary="The recommendation favored simpler infrastructure because the current scale did not justify heavier ops overhead.",
            ),
            ObservabilityTrace(
                id=f"{project_id}-trace-004",
                stage_key="evaluation_critique",
                agent_key="migration_critic",
                title="Migration Critic",
                status="succeeded",
                summary="Validated that the recommendation stayed aligned with evidence, cost sanity, and deployment safety gates.",
                confidence=0.91,
                latency_ms=205,
                evidence_count=3,
                evaluation_summary="Critic passed with no unsupported claims promoted into the deployment plan.",
            ),
        ]

    def _build_legacycart(self) -> ProjectSeed:
        generated_at = datetime(2026, 4, 16, 10, 30, tzinfo=UTC)
        evidence = [
            EvidenceReference(
                id="ev-app-prod-db-secret",
                source_type="file",
                source_uri="demo-systems/legacycart/backend/config/application-prod.yml",
                excerpt='password: "REDACTED_FAKE_PROD_PASSWORD"',
                locator=EvidenceLocator(line_start=6, line_end=8),
                confidence=0.99,
            ),
            EvidenceReference(
                id="ev-jenkins-access-key",
                source_type="file",
                source_uri="demo-systems/legacycart/infra/jenkins/Jenkinsfile",
                excerpt="withEnv(['AWS_ACCESS_KEY_ID=AKIA...','AWS_SECRET_ACCESS_KEY=...'])",
                locator=EvidenceLocator(line_start=19, line_end=24),
                confidence=0.97,
            ),
            EvidenceReference(
                id="ev-logback-pii",
                source_type="log",
                source_uri="demo-systems/legacycart/logs/app.log",
                excerpt="user=alice@example.com Authorization=Bearer REDACTED_FAKE_TOKEN cookie=sessionid=REDACTED_FAKE_COOKIE",
                locator=EvidenceLocator(line_start=1, line_end=1),
                confidence=0.94,
            ),
            EvidenceReference(
                id="ev-nfs-invoices",
                source_type="file",
                source_uri="demo-systems/legacycart/jobs/invoice-export.py",
                excerpt='output = Path("/mnt/shared/invoices") / f"{invoice_id}.pdf"',
                locator=EvidenceLocator(line_start=5, line_end=6),
                confidence=0.92,
            ),
            EvidenceReference(
                id="ev-compose-plaintext-db",
                source_type="manifest",
                source_uri="demo-systems/legacycart/infra/docker-compose.yml",
                excerpt='DATABASE_URL=postgres://legacycart:legacycart@postgres:5432/legacycart',
                locator=EvidenceLocator(line_start=28, line_end=32),
                confidence=0.91,
            ),
            EvidenceReference(
                id="ev-cron-direct-db",
                source_type="file",
                source_uri="demo-systems/legacycart/jobs/nightly_reconcile.sh",
                excerpt='psql -h postgres.legacycart.local -U legacycart_recon -d legacycart -c "select count(*) from orders;"',
                locator=EvidenceLocator(line_start=4, line_end=4),
                confidence=0.89,
            ),
            EvidenceReference(
                id="ev-java8-runtime",
                source_type="file",
                source_uri="demo-systems/legacycart/backend/config/application-prod.yml",
                excerpt='jdk: "Java 8"',
                locator=EvidenceLocator(line_start=12, line_end=13),
                confidence=0.95,
            ),
            EvidenceReference(
                id="ev-soap-basic-auth",
                source_type="file",
                source_uri="demo-systems/legacycart/integrations/payment-gateway/soap-client.wsdl",
                excerpt="Legacy gateway integration requires static IP allowlist and BasicAuth header.",
                locator=EvidenceLocator(line_start=1, line_end=3),
                confidence=0.84,
            ),
        ]

        evidence_by_id = {item.id: item for item in evidence}
        findings = [
            Finding(
                id="find-hardcoded-db-secret",
                title="Production database credentials are hardcoded",
                category="secrets",
                severity="critical",
                confidence=0.98,
                summary="LegacyCart keeps production PostgreSQL credentials in a committed profile file, preventing a safe lift-and-shift.",
                recommendation="Move secrets into a vault, rotate exposed credentials, and gate access through short-lived identities before any cloud cutover.",
                evidence=[evidence_by_id["ev-app-prod-db-secret"], evidence_by_id["ev-compose-plaintext-db"]],
            ),
            Finding(
                id="find-jenkins-long-lived-creds",
                title="Deployment pipeline uses long-lived cloud credentials",
                category="identity",
                severity="high",
                confidence=0.95,
                summary="The Jenkins pipeline exposes a broad AWS access key, making the current delivery path incompatible with approval-gated cloud operations.",
                recommendation="Replace static deploy credentials with assumed roles or workload identity and split deploy, ops, and DBA permissions.",
                evidence=[evidence_by_id["ev-jenkins-access-key"]],
            ),
            Finding(
                id="find-pii-logging",
                title="Sensitive data leaks into production logs",
                category="security",
                severity="high",
                confidence=0.93,
                summary="Logback is configured to emit customer email and authorization headers, creating compliance and incident-response exposure.",
                recommendation="Redact or drop sensitive fields, reduce log verbosity, and add structured audit-safe logging before migration.",
                evidence=[evidence_by_id["ev-logback-pii"]],
            ),
            Finding(
                id="find-nfs-storage",
                title="Invoice exports depend on shared NFS storage",
                category="storage",
                severity="medium",
                confidence=0.9,
                summary="Invoice generation writes directly to a legacy NFS path without lifecycle policy, encryption guarantee, or DR controls.",
                recommendation="Move exported documents to encrypted object storage with lifecycle, retention, and signed access patterns.",
                evidence=[evidence_by_id["ev-nfs-invoices"]],
            ),
            Finding(
                id="find-cron-coupling",
                title="Nightly reconciliation job is tightly coupled to a single host",
                category="operations",
                severity="medium",
                confidence=0.88,
                summary="Critical nightly reconciliation requires direct database access from a shell job, increasing cutover and rollback risk.",
                recommendation="Rebuild nightly jobs as queue-backed workers with retry, metrics, and environment-isolated credentials.",
                evidence=[evidence_by_id["ev-cron-direct-db"]],
            ),
            Finding(
                id="find-legacy-runtime",
                title="Core runtime is on Java 8",
                category="runtime",
                severity="medium",
                confidence=0.94,
                summary="The backend runs on Java 8, which raises support, patching, and container base-image constraints for a modern landing zone.",
                recommendation="Upgrade to a supported JDK baseline before container hardening and production Kubernetes planning.",
                evidence=[evidence_by_id["ev-java8-runtime"]],
            ),
        ]

        graph = DependencyGraph(
            generated_at=generated_at,
            summary="LegacyCart is anchored by a Spring monolith, PostgreSQL, shared file storage, shell jobs, and a Jenkins pipeline with brittle external dependencies.",
            nodes=[
                DependencyNode(
                    id="node-backend",
                    label="LegacyCart API",
                    kind="service",
                    environment="legacy",
                    status="at_risk",
                    x=120,
                    y=140,
                ),
                DependencyNode(
                    id="node-admin-ui",
                    label="AngularJS Admin",
                    kind="service",
                    environment="legacy",
                    status="at_risk",
                    x=120,
                    y=40,
                ),
                DependencyNode(
                    id="node-postgres",
                    label="PostgreSQL 9.x",
                    kind="database",
                    environment="legacy",
                    status="at_risk",
                    x=360,
                    y=140,
                ),
                DependencyNode(
                    id="node-invoice-store",
                    label="Shared NFS Invoice Store",
                    kind="storage",
                    environment="legacy",
                    status="at_risk",
                    x=370,
                    y=50,
                ),
                DependencyNode(
                    id="node-reconcile-job",
                    label="Nightly Reconcile",
                    kind="job",
                    environment="legacy",
                    status="at_risk",
                    x=120,
                    y=250,
                ),
                DependencyNode(
                    id="node-jenkins",
                    label="Jenkins Pipeline",
                    kind="pipeline",
                    environment="legacy",
                    status="at_risk",
                    x=360,
                    y=250,
                ),
                DependencyNode(
                    id="node-payment",
                    label="SOAP Payment Gateway",
                    kind="external_api",
                    environment="legacy",
                    status="observed",
                    x=600,
                    y=140,
                ),
                DependencyNode(
                    id="node-target-eks",
                    label="AWS App Platform",
                    kind="service",
                    environment="target",
                    status="planned",
                    x=640,
                    y=40,
                ),
            ],
            edges=[
                DependencyEdge(id="edge-ui-api", source="node-admin-ui", target="node-backend", relation="calls"),
                DependencyEdge(id="edge-api-db", source="node-backend", target="node-postgres", relation="reads_from"),
                DependencyEdge(id="edge-api-db-write", source="node-backend", target="node-postgres", relation="writes_to"),
                DependencyEdge(id="edge-api-nfs", source="node-backend", target="node-invoice-store", relation="writes_to"),
                DependencyEdge(id="edge-job-db", source="node-reconcile-job", target="node-postgres", relation="depends_on"),
                DependencyEdge(id="edge-job-api", source="node-reconcile-job", target="node-backend", relation="depends_on"),
                DependencyEdge(id="edge-pipeline-api", source="node-jenkins", target="node-backend", relation="deployed_via"),
                DependencyEdge(id="edge-api-payment", source="node-backend", target="node-payment", relation="calls"),
            ],
        )

        overview = ProjectOverview(
            id="legacycart",
            name="LegacyCart Modernization",
            client_name="Northstar Retail Group",
            readiness_score=52,
            migration_decision="Defer until blockers are remediated",
            confidence=0.88,
            phase="assessment",
            status="attention_required",
            recommended_provider="AWS",
        )

        local_credential = CredentialRef(
            id="cred-local-directory",
            kind="none",
            label="Read-only local scan",
            redacted_value="none",
        )
        github_credential = CredentialRef(
            id="cred-github",
            kind="oauth",
            label="GitHub connector token",
            redacted_value="gho_****",
            expires_at=datetime(2026, 5, 1, 0, 0, tzinfo=UTC),
        )
        azure_credential = CredentialRef(
            id="cred-azure-repos",
            kind="oauth",
            label="Azure DevOps connector token",
            redacted_value="ado_****",
            expires_at=datetime(2026, 5, 1, 0, 0, tzinfo=UTC),
        )
        aws_credential = CredentialRef(
            id="cred-aws",
            kind="assumed_role",
            label="AWS dry-run role",
            redacted_value="arn:aws:iam::123456789012:role/CockpitDryRun",
        )
        gcp_credential = CredentialRef(
            id="cred-gcp",
            kind="token",
            label="GCP discovery token",
            redacted_value="gcp_****",
        )
        azure_cloud_credential = CredentialRef(
            id="cred-azure-cloud",
            kind="access_key",
            label="Azure discovery key",
            redacted_value="azr_****",
        )

        source_connections = [
            SourceConnection(
                id="source-local-directory",
                kind="local_directory",
                name="Local directory",
                status="connected",
                mode="read_only",
                target="demo-systems/legacycart",
                last_sync_at=generated_at,
                credential_ref=local_credential,
                notes=["Read-only scan of the seeded demo system.", "Evidence stays local until a project-scoped source is approved."],
            ),
            SourceConnection(
                id="source-github",
                kind="github",
                name="GitHub repository",
                status="needs_attention",
                mode="discovery",
                target="github.com/northstar-retail/legacycart",
                branch="main",
                credential_ref=github_credential,
                notes=["Connector is configured for discovery only.", "Explicit repository access is still required."],
            ),
            SourceConnection(
                id="source-azure-repos",
                kind="azure_repos",
                name="Azure Repos",
                status="proposed",
                mode="approval_gated",
                target="dev.azure.com/northstar-retail/legacycart",
                branch="main",
                credential_ref=azure_credential,
                notes=["Requested by the tool gap detector.", "Remains disabled until approval and credentials are supplied."],
            ),
        ]

        cloud_connections = [
            CloudConnection(
                id="cloud-aws",
                provider="aws",
                name="AWS execution workspace",
                status="connected",
                mode="discovery",
                account_label="Northstar Retail - Migration Sandbox",
                region_scope=["us-east-1"],
                credential_ref=aws_credential,
                notes=["Discovery is enabled for the seeded demo.", "Execution remains approval gated."],
            ),
            CloudConnection(
                id="cloud-gcp",
                provider="gcp",
                name="GCP evaluation workspace",
                status="needs_attention",
                mode="dry_run",
                account_label="Northstar Retail - GCP Sandbox",
                region_scope=["us-central1"],
                credential_ref=gcp_credential,
                notes=["Useful for comparison planning.", "Needs service account wiring before use."],
            ),
            CloudConnection(
                id="cloud-azure",
                provider="azure",
                name="Azure evaluation workspace",
                status="proposed",
                mode="approval_gated",
                account_label="Northstar Retail - Azure Sandbox",
                region_scope=["eastus"],
                credential_ref=azure_cloud_credential,
                notes=["Reserved for future multi-cloud planning.", "Inactive until the project approves it."],
            ),
        ]

        factory_proposals = [
            FactoryProposal(
                id="factory-azure-repos-connector",
                name="Azure Repos Source Connector",
                kind="connector",
                status="proposed",
                rationale="The project needs project-scoped Azure Repos ingestion before connector coverage is complete.",
                required_permissions=["repo:read", "oauth:azure-devops"],
                prompt_version="v1",
                scaffold_files=["services/api/app/connectors/azure_repos.py", "services/api/tests/test_azure_repos_connector.py"],
                approval_required=True,
            ),
            FactoryProposal(
                id="factory-cert-inventory",
                name="Certificate Inventory Collector",
                kind="tool",
                status="proposed",
                rationale="The planning workspace needs a stub to inventory TLS certificates and ingress readiness signals.",
                required_permissions=["network:read", "dns:read"],
                prompt_version="v1",
                scaffold_files=["services/api/app/tools/cert_inventory.py", "services/api/tests/test_cert_inventory.py"],
                approval_required=True,
            ),
        ]

        chat_messages = [
            ChatMessage(
                id="chat-001",
                author="Taylor Reed",
                role="human",
                created_at=generated_at,
                content="Can we see the planning-ready path without switching to execution yet?",
            ),
            ChatMessage(
                id="chat-002",
                author="Cockpit Assistant",
                role="ai",
                created_at=datetime(2026, 4, 16, 10, 31, tzinfo=UTC),
                content="Yes. The planning surface stays read-only until approval, but we can still enumerate the source, cloud, and factory stubs needed for the next phase.",
            ),
            ChatMessage(
                id="chat-003",
                author="Taylor Reed",
                role="human",
                created_at=datetime(2026, 4, 16, 10, 32, tzinfo=UTC),
                content="What happens if we approve planning today?",
            ),
            ChatMessage(
                id="chat-004",
                author="Cockpit Assistant",
                role="ai",
                created_at=datetime(2026, 4, 16, 10, 33, tzinfo=UTC),
                content="The approval flips the planning record to approved and writes an audit event, but cloud writes remain disabled until a later execution approval.",
            ),
        ]

        approvals = [
            ApprovalRecord(
                id="approval-assessment-closeout",
                phase="Assessment Signoff",
                state="approved",
                requested_by="Ava Patel",
                approver="Marcus Lim",
                comment="Proceed to planning once critical secrets and logging blockers are included in the backlog.",
                decided_at=generated_at,
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

        audit_events = [
            AuditEvent(
                id="audit-scan-start",
                actor="legacycart-worker",
                action="scan.started",
                entity_type="migration_project",
                entity_id="legacycart",
                created_at=generated_at,
                metadata={"source": "demo-systems/legacycart", "mode": "read_only"},
            ),
            AuditEvent(
                id="audit-scan-finish",
                actor="legacycart-worker",
                action="scan.completed",
                entity_type="migration_project",
                entity_id="legacycart",
                created_at=generated_at,
                metadata={"evidenceItems": "8", "findings": "6"},
            ),
            AuditEvent(
                id="audit-report-export",
                actor="system",
                action="report.generated",
                entity_type="report",
                entity_id="report-executive",
                created_at=generated_at,
                metadata={"format": "pdf"},
            ),
            AuditEvent(
                id="audit-factory-proposal",
                actor="tool-gap-detector",
                action="registry.proposed",
                entity_type="registry_entry",
                entity_id="reg-azure-repos-connector",
                created_at=generated_at,
                metadata={"reason": "Azure Repos discovery requested but not implemented in MVP"},
            ),
        ]

        registry_entries = [
            RegistryEntry(
                id="reg-intake-normalizer",
                name="Intake Normalizer Agent",
                kind="agent",
                status="enabled",
                required_permissions=["project:read"],
                rationale="Normalizes stakeholder goals and constraints into the assessment context.",
                version="1.0.0",
                proposed_by="system",
                enabled=True,
            ),
            RegistryEntry(
                id="reg-aws-execution-adapter",
                name="AWS Dry-Run Execution Adapter",
                kind="connector",
                status="disabled",
                required_permissions=["cloud:read", "cloud:plan", "approval:execution"],
                rationale="Prepared for stage 3 execution with approval-gated dry-run actions only.",
                version="0.1.0",
                proposed_by="system",
                enabled=False,
            ),
            RegistryEntry(
                id="reg-azure-repos-connector",
                name="Azure Repos Source Connector",
                kind="connector",
                status="proposed",
                required_permissions=["repo:read", "oauth:azure-devops"],
                rationale="Tool Gap Detector flagged Azure Repos ingestion as a requested but unsupported source connector.",
                version="0.1.0-proposed",
                proposed_by="Tool Gap Detector Agent",
                enabled=False,
            ),
            RegistryEntry(
                id="reg-tool-factory-scaffold",
                name="Tool Factory Scaffold: Certificate Inventory Collector",
                kind="tool",
                status="proposed",
                required_permissions=["network:read", "dns:read"],
                rationale="Generated stub stays disabled until approved; would gather TLS and DNS evidence for ingress readiness reviews.",
                version="0.1.0-proposed",
                proposed_by="Tool / Connector Scaffold Agent",
                enabled=False,
            ),
        ]

        artifacts = [
            ReportArtifact(
                id="artifact-executive-pdf",
                kind="executive_summary",
                title="Executive Summary PDF",
                format="pdf",
                description="Board-ready summary of readiness, provider recommendation, and phased next steps.",
                updated_at=generated_at,
            ),
            ReportArtifact(
                id="artifact-architecture-pdf",
                kind="architecture_recommendation",
                title="Architecture Recommendation PDF",
                format="pdf",
                description="Recommended landing zone architecture with approval gates and guardrails.",
                updated_at=generated_at,
            ),
            ReportArtifact(
                id="artifact-wave-plan-mermaid",
                kind="migration_wave_plan",
                title="Migration Wave Plan",
                format="mermaid",
                description="Wave-by-wave remediation and migration sequence.",
                updated_at=generated_at,
            ),
            ReportArtifact(
                id="artifact-cutover-rollback-pdf",
                kind="cutover_rollback",
                title="Cutover and Rollback Playbook",
                format="pdf",
                description="Controlled cutover checklist with rollback criteria.",
                updated_at=generated_at,
            ),
            ReportArtifact(
                id="artifact-ops-checklist-md",
                kind="operations_checklist",
                title="Operations Checklist",
                format="markdown",
                description="Operational readiness and approval checklist.",
                updated_at=generated_at,
            ),
            ReportArtifact(
                id="artifact-roadmap-mermaid",
                kind="diagram",
                title="Migration Wave Diagram",
                format="mermaid",
                description="Mermaid migration wave view covering remediation, platform, and cutover phases.",
                updated_at=generated_at,
            ),
            ReportArtifact(
                id="artifact-terraform-hcl",
                kind="terraform",
                title="AWS Landing Zone Terraform Starter",
                format="hcl",
                description="Starter Terraform snippet for VPC, subnets, EKS, RDS, and S3-based document storage.",
                updated_at=generated_at,
            ),
        ]

        reports = [
            Report(
                id="report-executive",
                kind="executive_summary",
                title="Executive Migration Summary",
                summary="LegacyCart should not begin cloud migration until critical secret-handling and logging blockers are remediated, after which a phased AWS plan becomes viable.",
                confidence=0.9,
                generated_at=generated_at,
                artifact_ids=["artifact-executive-pdf"],
                sections=[
                    ReportSection(
                        title="Decision",
                        body="Recommendation: defer migration work until security fixes, database guardrails, and delivery identity remediation are complete.",
                        citations=[evidence_by_id["ev-app-prod-db-secret"], evidence_by_id["ev-java8-runtime"]],
                    ),
                    ReportSection(
                        title="Why AWS First",
                        body="AWS best fits the target due to strong migration primitives, mature managed PostgreSQL, EKS/ECS flexibility, and a clear path from NFS to S3.",
                        citations=[evidence_by_id["ev-nfs-invoices"], evidence_by_id["ev-cron-direct-db"]],
                    ),
                ],
            ),
            Report(
                id="report-technical",
                kind="technical_dossier",
                title="Technical Migration Dossier",
                summary="Detailed technical dossier covering evidence, dependency graph, workload risks, provider trade-offs, and recommended landing zone architecture.",
                confidence=0.88,
                generated_at=generated_at,
                artifact_ids=["artifact-roadmap-mermaid", "artifact-terraform-hcl"],
                sections=[
                    ReportSection(
                        title="Current State",
                        body="LegacyCart consists of a Java monolith, AngularJS admin console, PostgreSQL, shared NFS storage, shell jobs, and Jenkins-based deployments.",
                        citations=[evidence_by_id["ev-java8-runtime"], evidence_by_id["ev-nfs-invoices"]],
                    ),
                    ReportSection(
                        title="Primary Blockers",
                        body="Hardcoded credentials, long-lived deploy keys, sensitive logging, and single-host cron dependencies create unacceptable migration risk without remediation.",
                        citations=[
                            evidence_by_id["ev-app-prod-db-secret"],
                            evidence_by_id["ev-jenkins-access-key"],
                            evidence_by_id["ev-logback-pii"],
                            evidence_by_id["ev-cron-direct-db"],
                        ],
                    ),
                ],
            ),
            Report(
                id="report-cost",
                kind="cost_report",
                title="Cost and ROI Report",
                summary="Current and target-state financials show a favorable payback once remediation removes the highest-cost operational constraints.",
                confidence=0.86,
                generated_at=generated_at,
                artifact_ids=[],
                sections=[
                    ReportSection(
                        title="Baseline Cost",
                        body="The current estate carries heavy operations overhead because jobs, storage, and database maintenance are manually managed.",
                        citations=[evidence_by_id["ev-compose-plaintext-db"], evidence_by_id["ev-cron-direct-db"]],
                    ),
                    ReportSection(
                        title="Investment Profile",
                        body="The target plan concentrates spend on managed database, object storage, and reduced operational toil.",
                        citations=[evidence_by_id["ev-nfs-invoices"], evidence_by_id["ev-java8-runtime"]],
                    ),
                ],
            ),
            Report(
                id="report-risk",
                kind="risk_report",
                title="Risk and Compliance Report",
                summary="Key operational and security controls must be remediated before planning can advance safely.",
                confidence=0.9,
                generated_at=generated_at,
                artifact_ids=[],
                sections=[
                    ReportSection(
                        title="Critical Risk",
                        body="Hardcoded credentials, long-lived keys, and sensitive logging are the highest-risk issues in the seed project.",
                        citations=[evidence_by_id["ev-app-prod-db-secret"], evidence_by_id["ev-jenkins-access-key"], evidence_by_id["ev-logback-pii"]],
                    ),
                    ReportSection(
                        title="Operational Risk",
                        body="Shared storage and host-coupled batch jobs add rollback and recovery risk during cutover.",
                        citations=[evidence_by_id["ev-nfs-invoices"], evidence_by_id["ev-cron-direct-db"]],
                    ),
                ],
            ),
            Report(
                id="report-architecture",
                kind="architecture_recommendation",
                title="Architecture Recommendation",
                summary="A staged AWS replatform with managed database, object storage, and hardened identities is the best fit for the seed project.",
                confidence=0.87,
                generated_at=generated_at,
                artifact_ids=["artifact-architecture-pdf"],
                sections=[
                    ReportSection(
                        title="Target Shape",
                        body="Use a landing zone, containerized application tier, managed PostgreSQL, and object storage for the migration target.",
                        citations=[evidence_by_id["ev-java8-runtime"], evidence_by_id["ev-nfs-invoices"]],
                    ),
                ],
            ),
            Report(
                id="report-wave-plan",
                kind="migration_wave_plan",
                title="Migration Wave Plan",
                summary="The project should move through remediation, platform foundation, and controlled cutover waves.",
                confidence=0.85,
                generated_at=generated_at,
                artifact_ids=["artifact-wave-plan-mermaid"],
                sections=[
                    ReportSection(
                        title="Wave 0",
                        body="Close blockers and rotate credentials before any cloud writes are enabled.",
                        citations=[evidence_by_id["ev-app-prod-db-secret"], evidence_by_id["ev-jenkins-access-key"]],
                    ),
                    ReportSection(
                        title="Wave 1",
                        body="Stand up the landing zone and introduce managed database and storage dependencies.",
                        citations=[evidence_by_id["ev-nfs-invoices"], evidence_by_id["ev-java8-runtime"]],
                    ),
                ],
            ),
            Report(
                id="report-cutover-rollback",
                kind="cutover_rollback",
                title="Cutover and Rollback Playbook",
                summary="Rollback steps remain explicit so the migration can pause or reverse without losing transactional integrity.",
                confidence=0.84,
                generated_at=generated_at,
                artifact_ids=["artifact-cutover-rollback-pdf"],
                sections=[
                    ReportSection(
                        title="Cutover Controls",
                        body="Promote traffic only after restore tests and job replay checks complete successfully.",
                        citations=[evidence_by_id["ev-cron-direct-db"], evidence_by_id["ev-soap-basic-auth"]],
                    ),
                ],
            ),
            Report(
                id="report-ops-checklist",
                kind="operations_checklist",
                title="Operations Readiness Checklist",
                summary="The runbook focuses on approvals, evidence collection, and reversible execution.",
                confidence=0.83,
                generated_at=generated_at,
                artifact_ids=["artifact-ops-checklist-md"],
                sections=[
                    ReportSection(
                        title="Readiness",
                        body="Keep execution disabled until planning approval lands and the security remediation list is closed.",
                        citations=[evidence_by_id["ev-logback-pii"], evidence_by_id["ev-app-prod-db-secret"]],
                    ),
                ],
            ),
        ]

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
