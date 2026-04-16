from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Literal, cast

from ..core.db import (
    ClientAccountRecord,
    OrganizationRecord,
    ProjectCatalogRecord,
    ProjectSnapshotRecord,
    WorkspaceRecord,
    init_db,
    session_scope,
)
from ..core.settings import get_settings
from ..services.demo_project import build_demo_project_seed
from .models import (
    ApprovalRecord,
    AssessmentRun,
    AuditEvent,
    ChatMessage,
    ChatMessageCreate,
    ClientAccountSummary,
    CloudConnection,
    CloudConnectionCreate,
    CredentialRef,
    DependencyGraph,
    FactoryProposal,
    OrganizationSummary,
    ProjectCreate,
    ProjectOverview,
    ProjectSeed,
    SourceConnection,
    SourceConnectionCreate,
    WorkspaceContext,
    WorkspaceSummary,
)


class SeedRepository:
    """SQL-backed repository for the local SaaS control plane and demo tenant."""

    def __init__(self) -> None:
        init_db()
        self._ensure_demo_bootstrap()

    def get_project(self, project_id: str) -> ProjectSeed:
        with session_scope() as session:
            record = session.get(ProjectSnapshotRecord, project_id)
            if record is None:
                raise KeyError(project_id)
            return ProjectSeed.model_validate_json(record.payload_json)

    def list_projects(self, workspace_id: str | None = None) -> list[ProjectOverview]:
        with session_scope() as session:
            payloads: list[str]
            if workspace_id is None:
                payloads = [record.payload_json for record in session.query(ProjectSnapshotRecord).all()]
            else:
                project_ids = [
                    record.id
                    for record in session.query(ProjectCatalogRecord)
                    .filter(ProjectCatalogRecord.workspace_id == workspace_id)
                    .all()
                ]
                payloads = []
                for project_id in project_ids:
                    snapshot = session.get(ProjectSnapshotRecord, project_id)
                    if snapshot is not None:
                        payloads.append(snapshot.payload_json)
        projects = [ProjectSeed.model_validate_json(payload).overview for payload in payloads]
        return sorted(projects, key=lambda project: project.id)

    def get_workspace_context(self, workspace_id: str) -> WorkspaceContext:
        with session_scope() as session:
            workspace_record = session.get(WorkspaceRecord, workspace_id)
            if workspace_record is None:
                raise KeyError(workspace_id)
            organization_record = session.get(OrganizationRecord, workspace_record.organization_id)
            if organization_record is None:
                raise KeyError(workspace_record.organization_id)

            client_records = (
                session.query(ClientAccountRecord)
                .filter(ClientAccountRecord.workspace_id == workspace_id)
                .order_by(ClientAccountRecord.name)
                .all()
            )
            project_records = (
                session.query(ProjectCatalogRecord)
                .filter(ProjectCatalogRecord.workspace_id == workspace_id)
                .order_by(ProjectCatalogRecord.name)
                .all()
            )

            workspace_summary = WorkspaceSummary(
                id=workspace_record.id,
                organization_id=workspace_record.organization_id,
                name=workspace_record.name,
                slug=workspace_record.slug,
                mode=cast(Literal["demo", "standard"], workspace_record.mode),
                project_count=len(project_records),
            )
            organization_summary = OrganizationSummary(
                id=organization_record.id,
                name=organization_record.name,
                slug=organization_record.slug,
                mode=cast(Literal["demo", "standard"], organization_record.mode),
            )
            client_summaries = [
                ClientAccountSummary(
                    id=record.id,
                    workspace_id=record.workspace_id,
                    name=record.name,
                    industry=record.industry,
                    primary_region=record.primary_region,
                    compliance_tags=json.loads(record.compliance_tags_json),
                )
                for record in client_records
            ]
            project_ids = [record.id for record in project_records]

        projects = [self.get_project(project_id).overview for project_id in project_ids]
        return WorkspaceContext(
            organization=organization_summary,
            workspace=workspace_summary,
            client_accounts=client_summaries,
            projects=projects,
        )

    def list_workspace_projects(self, workspace_id: str) -> list[ProjectOverview]:
        return self.get_workspace_context(workspace_id).projects

    def create_workspace_project(self, workspace_id: str, draft: ProjectCreate) -> ProjectOverview:
        context = self.get_workspace_context(workspace_id)
        now = datetime.now(UTC).replace(microsecond=0)
        project_id = self._unique_project_id(draft.name)
        client_account_id = self._unique_client_account_id(draft.client_name)
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
            graph=DependencyGraph(
                nodes=[],
                edges=[],
                generated_at=now,
                summary="No source evidence has been ingested yet.",
            ),
            source_connections=[],
            cloud_connections=[],
            factory_proposals=[
                FactoryProposal(
                    id=f"proposal-{project_id}-connector-registry",
                    name="Connector coverage review",
                    kind="tool",
                    status="proposed",
                    rationale="Run the tool-gap workflow after the first real source connection is configured.",
                    required_permissions=["project:read"],
                    prompt_version="2026-04-16-intake-v1",
                    scaffold_files=["services/api/tests/test_tool_gap_flow.py"],
                    approval_required=True,
                )
            ],
            chat_messages=[
                ChatMessage(
                    id=f"chat-{project_id}-001",
                    role="system",
                    author="Cloud Migration Cockpit",
                    created_at=now,
                    content="Project created. Complete intake, connect a source, and run the first assessment.",
                )
            ],
            approvals=[
                ApprovalRecord(
                    id=f"approval-{project_id}-planning",
                    phase="Planning Phase",
                    state="pending",
                    requested_by=draft.owner,
                ),
                ApprovalRecord(
                    id=f"approval-{project_id}-execution",
                    phase="Execution Phase",
                    state="not_required",
                    requested_by="system",
                ),
            ],
            audit_events=[
                AuditEvent(
                    id=f"audit-{project_id}-created",
                    actor=draft.owner,
                    action="project.created",
                    entity_type="migration_project",
                    entity_id=project_id,
                    created_at=now,
                    metadata={"workspaceId": workspace_id, "mode": context.workspace.mode},
                )
            ],
            registry_entries=[],
            reports=[],
            artifacts=[],
        )

        with session_scope() as session:
            session.add(
                ClientAccountRecord(
                    id=client_account_id,
                    workspace_id=workspace_id,
                    name=draft.client_name,
                    industry="TBD",
                    primary_region=draft.primary_region,
                    compliance_tags_json=json.dumps(draft.compliance_tags),
                )
            )
            session.add(
                ProjectCatalogRecord(
                    id=project_id,
                    workspace_id=workspace_id,
                    client_account_id=client_account_id,
                    name=draft.name,
                    slug=project_id,
                    owner=draft.owner,
                    source_system=draft.source_system,
                    target_system=draft.target_system,
                    business_summary=draft.business_summary,
                    readiness_score=overview.readiness_score,
                    migration_decision=overview.migration_decision,
                    confidence=overview.confidence,
                    phase=overview.phase,
                    status=overview.status,
                    recommended_provider=overview.recommended_provider,
                )
            )
            session.add(
                ProjectSnapshotRecord(
                    project_id=project_id,
                    payload_json=project.model_dump_json(by_alias=False),
                )
            )
        return overview

    def create_project(self, workspace_id: str, draft: ProjectCreate) -> ProjectOverview:
        return self.create_workspace_project(workspace_id, draft)

    def add_source_connection(self, project_id: str, draft: SourceConnectionCreate) -> SourceConnection:
        project = self.get_project(project_id)
        now = datetime.now(UTC).replace(microsecond=0)
        connection = SourceConnection(
            id=f"source-{draft.kind}-{len(project.source_connections) + 1}",
            kind=draft.kind,
            name=draft.name,
            status="connected" if draft.kind == "local_directory" else "needs_configuration",
            mode=draft.mode,
            target=draft.target,
            branch=draft.branch,
            last_sync_at=now if draft.kind == "local_directory" else None,
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
                created_at=now,
                metadata={"kind": draft.kind, "target": draft.target},
            )
        )
        self._persist_project(project)
        return connection

    def add_cloud_connection(self, project_id: str, draft: CloudConnectionCreate) -> CloudConnection:
        project = self.get_project(project_id)
        now = datetime.now(UTC).replace(microsecond=0)
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
                created_at=now,
                metadata={"provider": draft.provider, "accountLabel": draft.account_label},
            )
        )
        self._persist_project(project)
        return connection

    def add_chat_message(self, project_id: str, draft: ChatMessageCreate) -> ChatMessage:
        project = self.get_project(project_id)
        now = datetime.now(UTC).replace(microsecond=0)
        message = ChatMessage(
            id=f"chat-{len(project.chat_messages) + 1:03d}",
            role=draft.role,
            author=draft.author,
            created_at=now,
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
                created_at=now,
                metadata={"role": draft.role},
            )
        )
        self._persist_project(project)
        return message

    def add_assessment_run(self, project_id: str, run: AssessmentRun, triggered_by: str) -> AssessmentRun:
        project = self.get_project(project_id)
        now = datetime.now(UTC).replace(microsecond=0)
        project.assessment_runs.insert(0, run)
        project.audit_events.append(
            AuditEvent(
                id=f"audit-assessment-{len(project.audit_events) + 1}",
                actor=triggered_by,
                action="assessment.requested",
                entity_type="assessment_run",
                entity_id=run.id,
                created_at=now,
                metadata={"mode": run.mode},
            )
        )
        self._persist_project(project)
        return run

    def _ensure_demo_bootstrap(self) -> None:
        with session_scope() as session:
            record = session.get(ProjectSnapshotRecord, "legacycart")
            if record is None:
                if not get_settings().seed_demo_data:
                    return
                project = build_demo_project_seed()
                session.add(
                    ProjectSnapshotRecord(
                        project_id=project.overview.id,
                        payload_json=project.model_dump_json(by_alias=False),
                    )
                )
            else:
                project = ProjectSeed.model_validate_json(record.payload_json)
            self._ensure_demo_tenant_records(session, project)

    def _ensure_demo_tenant_records(self, session, project: ProjectSeed) -> None:
        if session.get(OrganizationRecord, "org-demo") is None:
            session.add(
                OrganizationRecord(
                    id="org-demo",
                    name="Cloud Migration Cockpit Demo Org",
                    slug="demo-org",
                    mode="demo",
                )
            )
        if session.get(WorkspaceRecord, "workspace-demo") is None:
            session.add(
                WorkspaceRecord(
                    id="workspace-demo",
                    organization_id="org-demo",
                    name="Demo Workspace",
                    slug="demo-workspace",
                    mode="demo",
                )
            )
        if session.get(ClientAccountRecord, "client-demo-northstar") is None:
            session.add(
                ClientAccountRecord(
                    id="client-demo-northstar",
                    workspace_id="workspace-demo",
                    name=project.overview.client_name,
                    industry="Retail",
                    primary_region="us-east-1",
                    compliance_tags_json=json.dumps(["PCI-lite", "Customer PII"]),
                )
            )
        if session.get(ProjectCatalogRecord, project.overview.id) is None:
            session.add(
                ProjectCatalogRecord(
                    id=project.overview.id,
                    workspace_id="workspace-demo",
                    client_account_id="client-demo-northstar",
                    name=project.overview.name,
                    slug=project.overview.id,
                    owner="Ava Patel",
                    source_system="demo-systems/legacycart",
                    target_system="AWS landing zone with phased modernization",
                    business_summary="Retail order management with batch invoicing, cron jobs, and brittle external integrations.",
                    readiness_score=project.overview.readiness_score,
                    migration_decision=project.overview.migration_decision,
                    confidence=project.overview.confidence,
                    phase=project.overview.phase,
                    status=project.overview.status,
                    recommended_provider=project.overview.recommended_provider,
                )
            )

    def _persist_project(self, project: ProjectSeed) -> None:
        with session_scope() as session:
            record = session.get(ProjectSnapshotRecord, project.overview.id)
            if record is None:
                session.add(
                    ProjectSnapshotRecord(
                        project_id=project.overview.id,
                        payload_json=project.model_dump_json(by_alias=False),
                    )
                )
            else:
                record.payload_json = project.model_dump_json(by_alias=False)
            catalog = session.get(ProjectCatalogRecord, project.overview.id)
            if catalog is not None:
                catalog.name = project.overview.name
                catalog.readiness_score = project.overview.readiness_score
                catalog.migration_decision = project.overview.migration_decision
                catalog.confidence = project.overview.confidence
                catalog.phase = project.overview.phase
                catalog.status = project.overview.status
                catalog.recommended_provider = project.overview.recommended_provider

    def save_project(self, project: ProjectSeed) -> ProjectSeed:
        self._persist_project(project)
        return project

    def _unique_project_id(self, name: str) -> str:
        base = self._slugify(name)
        candidate = base
        index = 2
        existing_ids = {project.id for project in self.list_projects()}
        while candidate in existing_ids:
            candidate = f"{base}-{index}"
            index += 1
        return candidate

    def _unique_client_account_id(self, client_name: str) -> str:
        base = f"client-{self._slugify(client_name)}"
        candidate = base
        index = 2
        with session_scope() as session:
            existing_ids = {record.id for record in session.query(ClientAccountRecord).all()}
        while candidate in existing_ids:
            candidate = f"{base}-{index}"
            index += 1
        return candidate

    @staticmethod
    def _slugify(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "project"
