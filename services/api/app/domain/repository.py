from __future__ import annotations

from datetime import UTC, datetime

from .models import (
    AssessmentRun,
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
    ProjectOverview,
    ProjectSeed,
    SourceConnection,
    RegistryEntry,
    Report,
    ReportArtifact,
    ReportSection,
    SourceConnectionCreate,
    CloudConnectionCreate,
    ChatMessageCreate,
)


class SeedRepository:
    """In-memory repository with a deterministic seeded legacy migration project."""

    def __init__(self) -> None:
        self._project = self._build_legacycart()

    def get_project(self, project_id: str) -> ProjectSeed:
        if project_id != self._project.overview.id:
            raise KeyError(project_id)
        return self._project

    def list_projects(self) -> list[ProjectOverview]:
        return [self._project.overview]

    def add_source_connection(self, project_id: str, draft: SourceConnectionCreate) -> SourceConnection:
        project = self.get_project(project_id)
        connection = SourceConnection(
            id=f"source-{draft.kind}-{len(project.source_connections) + 1}",
            kind=draft.kind,
            name=draft.name,
            status="connected",
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
        return connection

    def add_cloud_connection(self, project_id: str, draft: CloudConnectionCreate) -> CloudConnection:
        project = self.get_project(project_id)
        connection = CloudConnection(
            id=f"cloud-{draft.provider}-{len(project.cloud_connections) + 1}",
            provider=draft.provider,
            name=draft.name,
            status="connected",
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
        return run

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
