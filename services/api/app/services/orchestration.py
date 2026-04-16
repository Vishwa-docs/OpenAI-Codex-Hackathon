from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from ..core.settings import get_settings
from ..domain.models import (
    AgentOutput,
    AgentRun,
    ApprovalDecision,
    ApprovalRecord,
    AssessmentBundle,
    AssessmentRun,
    AssessmentRunCreate,
    AuditEvent,
    ChatMessage,
    ChatMessageCreate,
    CloudConnection,
    CloudConnectionCreate,
    CostRoiSummary,
    DashboardSummary,
    EvalMetric,
    EvalRun,
    EvidenceReference,
    FactoryProposal,
    FinalRecommendation,
    Finding,
    PipelineSummary,
    ProjectCreate,
    ProjectOverview,
    ProviderOption,
    RegistryEntry,
    RiskComplianceSummary,
    RiskItem,
    Scenario,
    ScenarioDiff,
    ScenarioOutcome,
    SourceConnection,
    SourceConnectionCreate,
    WorkspaceContext,
)
from ..domain.repository import SeedRepository
from .chat import EvidenceGroundedChatService


@dataclass
class AssessmentContext:
    overview: ProjectOverview
    findings: list[Finding]
    evidence: list[EvidenceReference]
    registry_entries: list[RegistryEntry]


class AssessmentOrchestrator:
    """Assessment orchestration service for the local SaaS control plane."""

    def __init__(
        self,
        repository: SeedRepository,
        chat_service: EvidenceGroundedChatService | None = None,
    ) -> None:
        self.repository = repository
        self.chat_service = chat_service or EvidenceGroundedChatService(get_settings())

    def get_dashboard_summary(self) -> DashboardSummary:
        projects = self.repository.list_projects()
        pending_approvals = 0
        open_findings = 0
        report_exports = 0
        for project in projects:
            seed = self.repository.get_project(project.id)
            pending_approvals += sum(1 for item in seed.approvals if item.state == "pending")
            open_findings += len(seed.findings)
            report_exports += len([item for item in seed.artifacts if item.format == "pdf"])
        return DashboardSummary(
            active_projects=len(projects),
            pending_approvals=pending_approvals,
            open_findings=open_findings,
            report_exports=report_exports,
            top_projects=projects,
        )

    def build_assessment(self, project_id: str) -> AssessmentBundle:
        seed = self.repository.get_project(project_id)
        completed_at = datetime.now(UTC).replace(microsecond=0)
        started_at = completed_at.replace(second=max(0, completed_at.second - 18))
        ctx = AssessmentContext(
            overview=seed.overview,
            findings=seed.findings,
            evidence=seed.evidence,
            registry_entries=seed.registry_entries,
        )
        if not seed.evidence or not seed.findings:
            return self._build_pending_assessment_bundle(
                project_id=project_id,
                seed=seed,
                started_at=started_at,
                completed_at=completed_at,
            )
        provider_options = self._build_provider_options(ctx)
        cost_roi = self._build_cost_roi(ctx)
        risk_compliance = self._build_risk_summary(ctx)
        scenarios = self._build_scenarios(ctx)
        scenario_diffs = self._build_scenario_diffs(scenarios)
        agent_outputs = self._run_agents(ctx, provider_options, cost_roi, risk_compliance, scenarios)
        final_recommendation = self._aggregate_final(ctx, provider_options, risk_compliance, agent_outputs)
        pipeline_summaries = self._build_pipeline_summaries(started_at, completed_at)
        run = AssessmentRun(
            id=f"run-{project_id}-sync",
            project_id=project_id,
            status="succeeded",
            started_at=started_at,
            completed_at=completed_at,
            mode="sync",
            pipeline_summaries=pipeline_summaries,
            agent_outputs=agent_outputs,
            final_recommendation=final_recommendation,
        )
        return AssessmentBundle(
            run=run,
            overview=seed.overview,
            dashboard=self.get_dashboard_summary(),
            graph=seed.graph,
            findings=seed.findings,
            provider_options=provider_options,
            cost_roi=cost_roi,
            risk_compliance=risk_compliance,
            scenarios=scenarios,
            scenario_diffs=scenario_diffs,
            reports=seed.reports,
            artifacts=seed.artifacts,
            approvals=seed.approvals,
            audit_events=seed.audit_events,
            registry_entries=seed.registry_entries,
        )

    def list_source_connections(self, project_id: str) -> list[SourceConnection]:
        return self.repository.get_project(project_id).source_connections

    def get_workspace_context(self, workspace_id: str) -> WorkspaceContext:
        return self.repository.get_workspace_context(workspace_id)

    def list_workspace_projects(self, workspace_id: str) -> list[ProjectOverview]:
        return self.repository.list_workspace_projects(workspace_id)

    def create_workspace_project(self, workspace_id: str, draft: ProjectCreate) -> ProjectOverview:
        return self.repository.create_workspace_project(workspace_id, draft)

    def create_source_connection(
        self,
        project_id: str,
        draft: SourceConnectionCreate,
    ) -> SourceConnection:
        return self.repository.add_source_connection(project_id, draft)

    def list_cloud_connections(self, project_id: str) -> list[CloudConnection]:
        return self.repository.get_project(project_id).cloud_connections

    def create_cloud_connection(
        self,
        project_id: str,
        draft: CloudConnectionCreate,
    ) -> CloudConnection:
        return self.repository.add_cloud_connection(project_id, draft)

    def list_assessment_runs(self, project_id: str) -> list[AssessmentRun]:
        seed = self.repository.get_project(project_id)
        default_run = self.build_assessment(project_id).run
        recorded_ids = {item.id for item in seed.assessment_runs}
        return list(seed.assessment_runs) + ([] if default_run.id in recorded_ids else [default_run])

    def create_assessment_run(
        self,
        project_id: str,
        request: AssessmentRunCreate,
    ) -> AssessmentRun:
        bundle = self.build_assessment(project_id)
        run_number = len(self.repository.get_project(project_id).assessment_runs) + 1
        run = bundle.run.model_copy(
            update={
                "id": f"run-{project_id}-{request.mode.replace('_', '-')}-{run_number:03d}",
                "mode": request.mode,
                "started_at": datetime.now(UTC).replace(microsecond=0),
                "completed_at": datetime.now(UTC).replace(microsecond=0),
            }
        )
        return self.repository.add_assessment_run(project_id, run, request.triggered_by)

    def list_agent_runs(self, project_id: str) -> list[AgentRun]:
        bundle = self.build_assessment(project_id)
        runs = [self._agent_run_from_output(bundle.run.id, item) for item in bundle.run.agent_outputs]
        runs.append(
            AgentRun(
                id=f"{bundle.run.id}-iam-secrets-posture",
                assessment_run_id=bundle.run.id,
                agent_key="iam_secrets_posture",
                display_name="IAM & Secrets Posture Agent",
                stage="analysis",
                status="succeeded",
                critic=False,
                confidence=0.9,
                summary="Confirmed the source and cloud access model still requires approval-gated planning before any execution writes are enabled.",
                evidence_count=2,
                latency_ms=290,
                warning_count=0,
                retry_count=0,
                started_at=bundle.run.started_at,
                completed_at=bundle.run.completed_at,
            )
        )
        return runs

    def list_eval_runs(self, project_id: str) -> list[EvalRun]:
        bundle = self.build_assessment(project_id)
        metrics = [
            EvalMetric(
                metric_key="citation_coverage",
                label="Citation coverage",
                score=100,
                summary="All surfaced claims remain linked to evidence references.",
                status="pass",
            ),
            EvalMetric(
                metric_key="unsupported_claim_rate",
                label="Unsupported claim rate",
                score=98,
                summary="No unsupported claims were promoted into the current surfaced outputs.",
                status="pass",
            ),
            EvalMetric(
                metric_key="recommendation_consistency",
                label="Recommendation consistency",
                score=96,
                summary="Agent synthesis remains aligned on a defer-first recommendation.",
                status="pass",
            ),
            EvalMetric(
                metric_key="policy_compliance",
                label="Policy compliance",
                score=94,
                summary="Read-only discovery and approval-gated planning remain intact.",
                status="pass",
            ),
        ]
        return [
            EvalRun(
                id=f"{bundle.run.id}-eval",
                assessment_run_id=bundle.run.id,
                overall_score=97,
                status="succeeded",
                completed_at=bundle.run.completed_at,
                metrics=metrics,
            )
        ]

    def list_factory_proposals(self, project_id: str) -> list[FactoryProposal]:
        return self.repository.get_project(project_id).factory_proposals

    def list_chat_messages(self, project_id: str) -> list[ChatMessage]:
        return self.repository.get_project(project_id).chat_messages

    def create_chat_message(self, project_id: str, draft: ChatMessageCreate) -> ChatMessage:
        message = self.repository.add_chat_message(project_id, draft)
        if draft.role == "human":
            project = self.repository.get_project(project_id)
            assistant_reply = self.chat_service.build_reply(project, draft.content)
            self.repository.add_chat_message(
                project_id,
                ChatMessageCreate(
                    role="ai",
                    author="Cockpit Assistant",
                    content=assistant_reply,
                ),
            )
        return message

    def list_scenario_diffs(self, project_id: str) -> list[ScenarioDiff]:
        return self._build_scenario_diffs(self.build_assessment(project_id).scenarios)

    def decide_approval(self, project_id: str, approval_id: str, decision: ApprovalDecision) -> ApprovalRecord:
        seed = self.repository.get_project(project_id)
        approval = next((item for item in seed.approvals if item.id == approval_id), None)
        if approval is None:
            raise KeyError(approval_id)

        approval.state = decision.decision
        approval.approver = decision.actor
        approval.comment = decision.comment
        approval.decided_at = datetime(2026, 4, 16, 10, 45, tzinfo=UTC)

        seed.audit_events.append(
            AuditEvent(
                id=f"audit-{approval_id}-decision",
                actor=decision.actor,
                action="approval.decided",
                entity_type="approval",
                entity_id=approval_id,
                created_at=datetime(2026, 4, 16, 10, 45, 10, tzinfo=UTC),
                metadata={
                    "decision": decision.decision,
                    "comment": decision.comment,
                    "approvalId": approval_id,
                },
            )
        )
        self.repository.save_project(seed)
        return approval

    def _build_pending_assessment_bundle(
        self,
        project_id: str,
        seed,
        started_at: datetime,
        completed_at: datetime,
    ) -> AssessmentBundle:
        pipeline_summaries = [
            PipelineSummary(
                pipeline_key="intake_connections",
                title="Intake connections",
                status="running",
                summary="Business context is captured, but source and cloud connections still need validation before assessment can begin.",
                started_at=started_at,
            ),
            PipelineSummary(
                pipeline_key="evidence_ingestion",
                title="Evidence ingestion",
                status="blocked",
                summary="No normalized evidence exists yet. Connect a repository or local directory and trigger a scan.",
            ),
            PipelineSummary(
                pipeline_key="assessment_swarm",
                title="Assessment swarm",
                status="blocked",
                summary="Assessment agents are waiting for evidence-backed inputs from the worker pipeline.",
            ),
            PipelineSummary(
                pipeline_key="planning_artifacts",
                title="Planning artifacts",
                status="blocked",
                summary="Planning artifacts remain unavailable until the first assessment completes.",
            ),
            PipelineSummary(
                pipeline_key="report_composition",
                title="Report composition",
                status="blocked",
                summary="Reports and exports are generated only after the assessment dossier exists.",
            ),
            PipelineSummary(
                pipeline_key="evals_governance",
                title="Evals and governance",
                status="queued",
                summary="Critic checks and eval scoring will run after the first assessment run is completed.",
            ),
        ]
        provider_options = [
            ProviderOption(
                id="aws",
                name="AWS",
                score=74,
                best_for="The first live execution adapter and the default landing-zone baseline for new projects.",
                tradeoffs=["Provider choice should be revisited after discovery", "Current score is based on intake data only"],
                rationale="AWS stays the default planning baseline until source evidence and cloud inventory refine the recommendation.",
                confidence=0.58,
                evidence=[],
            ),
            ProviderOption(
                id="gcp",
                name="Google Cloud",
                score=68,
                best_for="Lean managed-service footprints for application and data modernization programs.",
                tradeoffs=["No source evidence has been ingested yet", "Current ranking is advisory only"],
                rationale="GCP remains a viable alternative, but there is not enough project evidence yet for a stronger recommendation.",
                confidence=0.5,
                evidence=[],
            ),
            ProviderOption(
                id="azure",
                name="Azure",
                score=67,
                best_for="Enterprise governance and Microsoft-heavy operating environments.",
                tradeoffs=["No source evidence has been ingested yet", "Current ranking is advisory only"],
                rationale="Azure remains in scope for comparison, pending workload evidence and connector data.",
                confidence=0.5,
                evidence=[],
            ),
        ]
        cost_roi = CostRoiSummary(
            annual_baseline_cost=0,
            annual_target_cost=0,
            migration_investment=0,
            annual_savings=0,
            payback_months=0,
            roi_percent=0,
            summary="Cost and ROI scoring is waiting for source discovery, workload shape, and environment evidence.",
            confidence=0.32,
            assumptions=["Connect a source system before treating any estimate as actionable."],
            evidence=[],
        )
        risk_summary = RiskComplianceSummary(
            overall_risk="moderate",
            compliance_frameworks=["Pending intake validation"],
            data_residency="Data residency posture cannot be finalized until regions, workloads, and storage paths are validated.",
            operational_readiness="Initial intake exists, but no evidence-backed operational readiness verdict is available yet.",
            risks=[
                RiskItem(
                    id="risk-missing-evidence",
                    severity="medium",
                    domain="assessment",
                    title="Assessment evidence has not been collected yet",
                    impact="Migration guidance would be speculative until the worker ingests repository, runtime, and configuration evidence.",
                    mitigation="Connect a source and run the first assessment before presenting provider, cost, or risk decisions to stakeholders.",
                    confidence=0.78,
                    evidence=[],
                )
            ],
            summary="The project is safe to keep in intake, but not ready for evidence-backed migration recommendations.",
            confidence=0.55,
        )
        scenarios = [
            Scenario(
                id="scenario-connect-local",
                name="Connect a local source first",
                description="Validate the workload from a checked-out repository or filesystem path before comparing providers.",
                assumption_set=["A local or hosted source connection is available.", "The project owner can approve a read-only scan."],
                outcome=ScenarioOutcome(
                    readiness=42,
                    risk_delta="-15%",
                    cost_delta="n/a",
                    summary="Fastest path to evidence-backed guidance and the best next action for a newly created project.",
                ),
            )
        ]
        final_recommendation = FinalRecommendation(
            decision="defer",
            label="Assessment pending evidence ingestion",
            confidence=0.55,
            summary="Do not start migration planning yet. Capture source evidence first, then let the assessment swarm produce a cited recommendation.",
            recommended_provider="AWS",
            rationale=[
                "The project has intake data but no repository or runtime evidence yet.",
                "Provider, cost, and risk guidance would be too speculative without a worker scan.",
                "The control plane keeps planning and execution blocked until evidence exists.",
            ],
            blockers=["No connected source has been ingested.", "No assessment run has produced evidence-backed findings yet."],
            next_steps=[
                "Connect a local directory, GitHub repo, or Azure Repos project.",
                "Run the first assessment to populate evidence, findings, and reports.",
                "Review the resulting provider, cost, and risk recommendations before requesting planning approval.",
            ],
            evidence=[],
        )
        agent_outputs = [
            AgentOutput(
                agent_key="intake_normalizer",
                display_name="Intake Normalizer Agent",
                status="succeeded",
                confidence=0.71,
                summary="Captured the project scope and target environment, but flagged the dossier as intake-only until evidence arrives.",
                evidence=[],
                structured_output={"phase": "intake", "sourceConnected": False},
            ),
            AgentOutput(
                agent_key="safety_critic",
                display_name="Safety Critic Agent",
                status="succeeded",
                confidence=0.93,
                summary="Planning and execution remain safely blocked until the first evidence-backed assessment run is completed.",
                evidence=[],
                structured_output={"writeActionsDetected": 0, "requiresApproval": True, "executionEnabled": False},
            ),
        ]
        run = AssessmentRun(
            id=f"run-{project_id}-sync",
            project_id=project_id,
            status="queued",
            started_at=started_at,
            completed_at=completed_at,
            mode="sync",
            pipeline_summaries=pipeline_summaries,
            agent_outputs=agent_outputs,
            final_recommendation=final_recommendation,
        )
        return AssessmentBundle(
            run=run,
            overview=seed.overview,
            dashboard=self.get_dashboard_summary(),
            graph=seed.graph,
            findings=seed.findings,
            provider_options=provider_options,
            cost_roi=cost_roi,
            risk_compliance=risk_summary,
            scenarios=scenarios,
            scenario_diffs=[],
            reports=seed.reports,
            artifacts=seed.artifacts,
            approvals=seed.approvals,
            audit_events=seed.audit_events,
            registry_entries=seed.registry_entries,
        )

    def _run_agents(
        self,
        ctx: AssessmentContext,
        provider_options: list[ProviderOption],
        cost_roi: CostRoiSummary,
        risk_compliance: RiskComplianceSummary,
        scenarios: list[Scenario],
    ) -> list[AgentOutput]:
        grouped_evidence = self._top_evidence(ctx.evidence, count=3)
        highest_finding = sorted(ctx.findings, key=self._severity_rank)[0]
        top_findings = sorted(ctx.findings, key=self._severity_rank)[:3]
        proposed_entries = [
            item.model_dump(by_alias=True) for item in ctx.registry_entries if item.status == "proposed"
        ]
        return [
            AgentOutput(
                agent_key="intake_normalizer",
                display_name="Intake Normalizer Agent",
                status="succeeded",
                confidence=0.95,
                summary="Captured migration goal as phased modernization with strong security, rollback, and approval constraints.",
                evidence=grouped_evidence,
                structured_output={
                    "targetRegion": "us-east-1",
                    "complianceNeeds": ["PCI-lite", "customer PII protection"],
                    "executionMode": "approval_gated",
                },
            ),
            AgentOutput(
                agent_key="codebase_discovery",
                display_name="Codebase Discovery Agent",
                status="succeeded",
                confidence=0.92,
                summary="Identified a legacy web tier, backend service, PostgreSQL datastore, cron-style jobs, shared storage, and legacy pipeline assets.",
                evidence=self._select_evidence(ctx, ["java runtime", "postgres", "nfs"]),
                structured_output={"componentsDiscovered": 7, "legacyRuntimes": ["Java 8", "AngularJS 1.x"]},
            ),
            AgentOutput(
                agent_key="infra_manifest_analyzer",
                display_name="Infra Manifest Analyzer Agent",
                status="succeeded",
                confidence=0.9,
                summary="Infra manifests indicate host-coupled delivery, plaintext database connection patterns, and legacy network assumptions.",
                evidence=self._select_evidence(ctx, ["compose", "jenkins", "database url"]),
                structured_output={"manifestSignals": ["docker-compose", "jenkins", "legacy network assumptions"]},
            ),
            AgentOutput(
                agent_key="dependency_graph",
                display_name="Dependency Graph Agent",
                status="succeeded",
                confidence=0.91,
                summary="The dependency graph centers on the backend, PostgreSQL, shared invoice storage, and brittle external integration seams.",
                evidence=self._select_evidence(ctx, ["postgres", "nfs", "soap"]),
                structured_output={"criticalPaths": ["backend->postgres", "jobs->postgres", "backend->integration"]},
            ),
            AgentOutput(
                agent_key="database_data_store",
                display_name="Database & Data Store Analyzer Agent",
                status="succeeded",
                confidence=0.92,
                summary="PostgreSQL and shared invoice storage are the most important stateful migration surfaces and need controlled backup, restore, and cutover handling.",
                evidence=self._select_evidence(ctx, ["postgres", "invoices", "shared"]),
                structured_output={"primaryStores": ["PostgreSQL", "shared invoice storage"], "migrationPattern": "phased with restore validation"},
            ),
            AgentOutput(
                agent_key="runtime_ops_readiness",
                display_name="Runtime / Ops Readiness Agent",
                status="succeeded",
                confidence=0.89,
                summary="Operational readiness is partial because the runtime is legacy, jobs are host-coupled, and observability controls need hardening.",
                evidence=self._select_evidence(ctx, ["java runtime", "cron", "authorization"]),
                structured_output={"runtimeReadiness": "partial", "rollbackPreparedness": "needs_work"},
            ),
            AgentOutput(
                agent_key="security_secrets",
                display_name="Security & Secrets Agent",
                status="succeeded",
                confidence=0.97,
                summary="Flagged hardcoded production credentials, long-lived pipeline access keys, and sensitive log leakage as immediate blockers.",
                evidence=self._select_evidence(
                    ctx,
                    ["database credentials", "access key", "authorization cookie logs"],
                ),
                structured_output={
                    "criticalSecrets": 2,
                    "sensitiveLogging": True,
                    "highestSeverityFinding": highest_finding.title,
                },
            ),
            AgentOutput(
                agent_key="risk_compliance",
                display_name="Risk & Compliance Agent",
                status="succeeded",
                confidence=risk_compliance.confidence,
                summary=risk_compliance.summary,
                evidence=self._select_evidence(ctx, ["authorization cookie logs", "nfs invoices"]),
                structured_output=risk_compliance.model_dump(by_alias=True),
            ),
            AgentOutput(
                agent_key="cloud_recommendation",
                display_name="Cloud Recommendation Agent",
                status="succeeded",
                confidence=provider_options[0].confidence,
                summary=f"{provider_options[0].name} leads because it best supports phased modernization with managed database, object storage, and controlled container adoption.",
                evidence=provider_options[0].evidence,
                structured_output={"recommendedProvider": provider_options[0].id, "decisionStyle": "phased_replatform"},
            ),
            AgentOutput(
                agent_key="cost_roi",
                display_name="Cost & ROI Agent",
                status="succeeded",
                confidence=cost_roi.confidence,
                summary=cost_roi.summary,
                evidence=cost_roi.evidence,
                structured_output=cost_roi.model_dump(by_alias=True),
            ),
            AgentOutput(
                agent_key="architecture_planner",
                display_name="Architecture Planner Agent",
                status="succeeded",
                confidence=0.88,
                summary="Recommended a landing zone with isolated environments, managed data services, object storage, and approval-gated delivery controls.",
                evidence=self._select_evidence(ctx, ["postgres", "nfs", "access key"]),
                structured_output={"targetArchitecture": provider_options[0].name, "environmentStrategy": ["dev", "staging", "prod"]},
            ),
            AgentOutput(
                agent_key="container_kubernetes",
                display_name="Container / Kubernetes Planner Agent",
                status="succeeded",
                confidence=0.84,
                summary="Containerization is viable after runtime upgrades and secret remediation, with Kubernetes adoption gated behind ops maturity.",
                evidence=self._select_evidence(ctx, ["java runtime", "compose"]),
                structured_output={"containerizationReadiness": "conditional", "kubernetesReadiness": "later_phase"},
            ),
            AgentOutput(
                agent_key="devops_pipeline",
                display_name="DevOps Pipeline Agent",
                status="succeeded",
                confidence=0.87,
                summary="The current delivery path needs short-lived credentials, clearer approvals, and environment-aware promotion controls before cloud execution is enabled.",
                evidence=self._select_evidence(ctx, ["jenkins", "access key"]),
                structured_output={"deliveryGuardrails": ["short-lived credentials", "approval gates", "promotion controls"]},
            ),
            AgentOutput(
                agent_key="scenario_what_if",
                display_name="Scenario / What-if Agent",
                status="succeeded",
                confidence=0.86,
                summary="Prepared three migration paths that trade off speed, risk burn-down, and modernization investment.",
                evidence=self._select_evidence(ctx, ["cron database", "soap gateway"]),
                structured_output={"scenarioCount": len(scenarios)},
            ),
            AgentOutput(
                agent_key="report_composer",
                display_name="Report Composer Agent",
                status="succeeded",
                confidence=0.89,
                summary="Compiled executive, technical, risk, architecture, migration-wave, and operations views from the same evidence base.",
                evidence=grouped_evidence,
                structured_output={"reportFamilies": ["executive", "technical", "risk", "architecture", "roadmap", "operations"]},
            ),
            AgentOutput(
                agent_key="executive_summary",
                display_name="Executive Summary Agent",
                status="succeeded",
                confidence=0.9,
                summary=f"Prepared an executive framing around {ctx.overview.migration_decision.lower()} with {ctx.overview.recommended_provider} as the leading provider path.",
                evidence=grouped_evidence,
                structured_output={"headlineDecision": ctx.overview.migration_decision, "recommendedProvider": ctx.overview.recommended_provider},
            ),
            AgentOutput(
                agent_key="tool_gap_detector",
                display_name="Tool Gap Detector Agent",
                status="succeeded",
                confidence=0.84,
                summary="Detected connector and evidence-collection gaps that still need approved scaffold proposals before activation.",
                evidence=[],
                structured_output={
                    "proposedEntries": proposed_entries
                },
                limitations=["Scaffold proposals stay disabled until approved and implemented with the needed credentials."],
            ),
            AgentOutput(
                agent_key="tool_connector_scaffold",
                display_name="Tool / Connector Scaffold Agent",
                status="succeeded",
                confidence=0.82,
                summary="Prepared scaffold metadata for disabled registry proposals so they can be approved, tracked, and implemented safely.",
                evidence=[],
                structured_output={"proposalCount": len(proposed_entries), "proposals": proposed_entries},
            ),
            AgentOutput(
                agent_key="citation_evidence_critic",
                display_name="Citation / Evidence Critic Agent",
                status="succeeded",
                confidence=0.93,
                summary="Verified that all surfaced findings and recommendations carry direct citations; no unsupported claims were promoted to the final recommendation.",
                evidence=self._top_evidence(ctx.evidence, count=3),
                structured_output={
                    "citationCoverage": 1.0,
                    "unsupportedClaims": 0,
                    "missingEvidenceFlags": [],
                },
            ),
            AgentOutput(
                agent_key="safety_critic",
                display_name="Safety Critic Agent",
                status="succeeded",
                confidence=0.92,
                summary="Assessment remains read-only, approval-gated, and non-destructive; execution adapters stay disabled until a later phase.",
                evidence=[],
                structured_output={
                    "writeActionsDetected": 0,
                    "requiresApproval": True,
                    "executionEnabled": False,
                },
            ),
            AgentOutput(
                agent_key="final_recommendation_aggregator",
                display_name="Final Recommendation Aggregator",
                status="succeeded",
                confidence=round(sum(item.confidence for item in top_findings) / len(top_findings), 2),
                summary=(
                    f"Final synthesis recommends {ctx.overview.migration_decision.lower()} after closing the highest-risk blockers: "
                    + ", ".join(finding.title for finding in top_findings)
                ),
                evidence=grouped_evidence,
                structured_output={
                    "decision": ctx.overview.migration_decision,
                    "blockers": [finding.title for finding in top_findings],
                    "recommendedProvider": provider_options[0].name,
                },
            ),
        ]

    @staticmethod
    def _build_pipeline_summaries(
        started_at: datetime,
        completed_at: datetime,
    ) -> list[PipelineSummary]:
        return [
            PipelineSummary(
                pipeline_key="intake_connections",
                title="Intake connections",
                status="succeeded",
                summary="Project intake and connector context have been normalized for the current assessment run.",
                started_at=started_at,
                completed_at=completed_at,
            ),
            PipelineSummary(
                pipeline_key="evidence_ingestion",
                title="Evidence ingestion",
                status="succeeded",
                summary="Worker evidence has been normalized into canonical findings, citations, and graph inputs.",
                started_at=started_at,
                completed_at=completed_at,
            ),
            PipelineSummary(
                pipeline_key="assessment_swarm",
                title="Assessment swarm",
                status="succeeded",
                summary="Specialist agents completed their analysis pass over the current project evidence.",
                started_at=started_at,
                completed_at=completed_at,
            ),
            PipelineSummary(
                pipeline_key="planning_artifacts",
                title="Planning artifacts",
                status="blocked",
                summary="Planning artifacts remain approval gated until the planning decision is recorded.",
                started_at=started_at,
            ),
            PipelineSummary(
                pipeline_key="report_composition",
                title="Report composition",
                status="succeeded",
                summary="Executive, technical, and planning reports are ready for export from the current evidence set.",
                started_at=started_at,
                completed_at=completed_at,
            ),
            PipelineSummary(
                pipeline_key="evals_governance",
                title="Evals and governance",
                status="succeeded",
                summary="Critic checks, approval records, and governance metadata are available for review.",
                started_at=started_at,
                completed_at=completed_at,
            ),
        ]

    @staticmethod
    def _agent_run_from_output(assessment_run_id: str, output: AgentOutput) -> AgentRun:
        stage_map: dict[
            str,
            Literal["intake", "discovery", "analysis", "planning", "critique", "reporting"],
        ] = {
            "intake_normalizer": "intake",
            "codebase_discovery": "discovery",
            "infra_manifest_analyzer": "discovery",
            "dependency_graph": "discovery",
            "database_data_store": "analysis",
            "runtime_ops_readiness": "analysis",
            "security_secrets": "analysis",
            "risk_compliance": "analysis",
            "tool_gap_detector": "analysis",
            "cloud_recommendation": "planning",
            "cost_roi": "planning",
            "architecture_planner": "planning",
            "container_kubernetes": "planning",
            "devops_pipeline": "planning",
            "scenario_what_if": "planning",
            "tool_connector_scaffold": "planning",
            "citation_evidence_critic": "critique",
            "safety_critic": "critique",
            "report_composer": "reporting",
            "executive_summary": "reporting",
            "final_recommendation_aggregator": "reporting",
        }
        stage = stage_map.get(output.agent_key, "analysis")
        return AgentRun(
            id=f"{assessment_run_id}-{output.agent_key}",
            assessment_run_id=assessment_run_id,
            agent_key=output.agent_key,
            display_name=output.display_name,
            stage=stage,
            status=output.status,
            critic=output.agent_key.endswith("_critic"),
            confidence=output.confidence,
            summary=output.summary,
            evidence_count=len(output.evidence),
            latency_ms=240,
            warning_count=0,
            retry_count=0,
            started_at=datetime(2026, 4, 16, 10, 30, tzinfo=UTC),
            completed_at=datetime(2026, 4, 16, 10, 30, tzinfo=UTC),
        )

    def _build_provider_options(self, ctx: AssessmentContext) -> list[ProviderOption]:
        shared = self._select_evidence(ctx, ["nfs invoices", "cron database", "soap gateway"])
        return [
            ProviderOption(
                id="aws",
                name="AWS",
                score=86,
                best_for="Fastest path to a phased replatform with managed PostgreSQL, S3-backed document storage, and container adoption.",
                tradeoffs=["Requires IAM design discipline", "EKS can be heavy if the team is not container-ready on day one"],
                rationale="Best alignment with the requested AWS-first execution path and clear replacements for NFS, cron, and long-lived credentials.",
                confidence=0.9,
                evidence=shared,
            ),
            ProviderOption(
                id="gcp",
                name="Google Cloud",
                score=78,
                best_for="Operationally lean managed services and strong data platform ergonomics.",
                tradeoffs=["Weaker alignment with the requested AWS-first execution roadmap", "Legacy network and identity patterns would still need significant refactoring"],
                rationale="A credible option for App Engine/Cloud Run plus Cloud SQL, but less aligned to the planned execution adapters.",
                confidence=0.82,
                evidence=shared,
            ),
            ProviderOption(
                id="azure",
                name="Azure",
                score=74,
                best_for="Organizations with deep Microsoft identity and enterprise governance standards.",
                tradeoffs=["MVP lacks Azure Repos ingestion", "Current SOAP and batch patterns still need rework before a safe landing zone"],
                rationale="Viable for enterprise controls, but the current roadmap and evidence still fit AWS more naturally.",
                confidence=0.79,
                evidence=shared,
            ),
        ]

    def _build_cost_roi(self, ctx: AssessmentContext) -> CostRoiSummary:
        evidence = self._select_evidence(ctx, ["nfs invoices", "cron database", "java runtime"])
        return CostRoiSummary(
            annual_baseline_cost=168000,
            annual_target_cost=132000,
            migration_investment=95000,
            annual_savings=36000,
            payback_months=32,
            roi_percent=38,
            summary="A phased AWS migration lowers run-rate by replacing brittle VM/NFS operations with managed services, but remediation and platform work create a longer payback window than a pure lift-and-shift.",
            confidence=0.81,
            assumptions=[
                "Backend moves to containers in wave 2",
                "RDS replaces self-managed PostgreSQL",
                "Invoice storage moves to S3 with lifecycle policies",
            ],
            evidence=evidence,
        )

    def _build_risk_summary(self, ctx: AssessmentContext) -> RiskComplianceSummary:
        critical = RiskItem(
            id="risk-secret-exposure",
            severity="critical",
            domain="identity",
            title="Exposed credentials block safe migration execution",
            impact="Any infrastructure move would carry breach and privilege-escalation risk until secrets are rotated and moved out of source control.",
            mitigation="Vault secrets, rotate credentials, and adopt short-lived deployment identities before the planning phase closes.",
            confidence=0.97,
            evidence=self._select_evidence(ctx, ["database credentials", "access key"]),
        )
        logging = RiskItem(
            id="risk-pii-logs",
            severity="high",
            domain="compliance",
            title="PII and auth headers leak into logs",
            impact="Non-production-grade logging creates privacy exposure and undermines audit readiness.",
            mitigation="Implement structured redaction and tighten retention before wider cloud observability rollout.",
            confidence=0.93,
            evidence=self._select_evidence(ctx, ["authorization cookie logs"]),
        )
        ops = RiskItem(
            id="risk-ops-coupling",
            severity="medium",
            domain="operations",
            title="Batch operations depend on direct host access",
            impact="Cutover and rollback plans are fragile because nightly jobs assume direct shell and database access.",
            mitigation="Move jobs into queue-backed workers with observable retries and least-privilege credentials.",
            confidence=0.88,
            evidence=self._select_evidence(ctx, ["cron database", "nfs invoices"]),
        )
        return RiskComplianceSummary(
            overall_risk="high",
            compliance_frameworks=["PCI-lite", "customer PII protection", "internal audit"],
            data_residency="No hard blocker found for US-hosted deployment, but document retention and log hygiene need controls before production migration.",
            operational_readiness="Partial. Team can support a staged migration, but observability, backups, and runbooks must be upgraded before cutover.",
            risks=[critical, logging, ops],
            summary="Migration is feasible, but only after identity, logging, and operational coupling issues are addressed in a first remediation wave.",
            confidence=0.89,
        )

    def _build_scenarios(self, ctx: AssessmentContext) -> list[Scenario]:
        return [
            Scenario(
                id="scenario-security-first",
                name="Security-first migration",
                description="Resolve secrets, deploy identity, and logging exposure before any infra relocation.",
                assumption_set=[
                    "Rotate credentials before planning signoff",
                    "Delay containerization until after remediation",
                    "Hold cutover until audit-safe logging is live",
                ],
                outcome=ScenarioOutcome(
                    readiness=67,
                    risk_delta="-35%",
                    cost_delta="+8% upfront",
                    summary="Lowest execution risk and best board confidence, but slower time-to-cloud.",
                ),
            ),
            Scenario(
                id="scenario-lift-shift-guardrails",
                name="Lift-and-shift with guardrails",
                description="Containerize minimally, move core services quickly, then optimize after stabilization.",
                assumption_set=[
                    "Use managed PostgreSQL and object storage at cutover",
                    "Keep Jenkins temporarily with reduced credentials",
                    "Retain SOAP gateway behind an adapter",
                ],
                outcome=ScenarioOutcome(
                    readiness=61,
                    risk_delta="-18%",
                    cost_delta="-12% run rate after month 4",
                    summary="Fastest path to cloud presence, but keeps moderate platform debt alive longer.",
                ),
            ),
            Scenario(
                id="scenario-strangler",
                name="Strangler modernization",
                description="Split invoices, batch processing, and admin UI into phased services while the monolith remains online.",
                assumption_set=[
                    "Prioritize invoice storage and batch jobs in wave 1",
                    "Adopt containers and managed queues before full cutover",
                    "Budget for parallel-run validation",
                ],
                outcome=ScenarioOutcome(
                    readiness=72,
                    risk_delta="-40%",
                    cost_delta="+18% during overlap, then -20% after stabilization",
                    summary="Best long-term platform position, but highest short-term delivery complexity.",
                ),
            ),
        ]

    @staticmethod
    def _build_scenario_diffs(scenarios: list[Scenario]) -> list[ScenarioDiff]:
        if len(scenarios) < 3:
            return []
        baseline = scenarios[0]
        return [
            ScenarioDiff(
                baseline_scenario_id=baseline.id,
                compared_scenario_id=scenarios[1].id,
                readiness_delta=scenarios[1].outcome.readiness - baseline.outcome.readiness,
                risk_shift="Risk increases because security remediation is deferred deeper into the migration path.",
                cost_shift="Near-term spend is lower, but long-term carry cost rises as technical debt remains.",
                summary="Lift-and-shift with guardrails is faster, but the risk profile stays materially worse than the baseline.",
            ),
            ScenarioDiff(
                baseline_scenario_id=baseline.id,
                compared_scenario_id=scenarios[2].id,
                readiness_delta=scenarios[2].outcome.readiness - baseline.outcome.readiness,
                risk_shift="Risk stays controlled while long-term flexibility improves through phased seam extraction.",
                cost_shift="Program spend rises moderately because the modernization work is distributed across more waves.",
                summary="Strangler modernization preserves safety while improving long-term platform leverage.",
            ),
        ]

    def _aggregate_final(
        self,
        ctx: AssessmentContext,
        providers: list[ProviderOption],
        risk_summary: RiskComplianceSummary,
        agent_outputs: list[AgentOutput],
    ) -> FinalRecommendation:
        high_blockers = [finding.title for finding in ctx.findings if finding.severity in {"critical", "high"}]
        average_confidence = sum(output.confidence for output in agent_outputs) / len(agent_outputs)
        decision: Literal["migrate_now", "migrate_partially", "defer", "rearchitect_first"]
        if ctx.overview.readiness_score >= 75:
            decision = "migrate_now"
            label = "Migrate now"
        elif ctx.overview.readiness_score >= 65:
            decision = "migrate_partially"
            label = "Migrate partially"
        elif ctx.overview.readiness_score >= 50:
            decision = "defer"
            label = "Defer until blockers are remediated"
        else:
            decision = "rearchitect_first"
            label = "Re-architect first"
        return FinalRecommendation(
            decision=decision,
            label=label,
            confidence=round(average_confidence, 2),
            summary=(
                f"Current assessment outcome: {label}. Close wave-0 blockers first, then revisit a phased "
                f"{providers[0].name} migration once the highest-risk issues are remediated."
            ),
            recommended_provider=providers[0].name,
            rationale=[
                f"{providers[0].name} best supports the requested future execution model and staged modernization path.",
                "Managed PostgreSQL and S3 directly address the current database and NFS storage pain points.",
                f"The current overall risk is {risk_summary.overall_risk}, which is too high for direct execution without remediation.",
            ],
            blockers=high_blockers,
            next_steps=[
                "Rotate and externalize all exposed credentials.",
                "Redact sensitive fields from logs and add retention controls.",
                "Define a wave-1 landing zone with RDS, S3, VPC segmentation, and approval-gated CI/CD.",
            ],
            evidence=self._top_evidence(ctx.evidence, count=4),
        )

    @staticmethod
    def _severity_rank(finding: Finding) -> tuple[int, float]:
        rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        return rank[finding.severity], -finding.confidence

    @staticmethod
    def _select_evidence(ctx: AssessmentContext, evidence_ids: list[str]) -> list[EvidenceReference]:
        selected: list[EvidenceReference] = []
        seen_ids: set[str] = set()

        for hint in evidence_ids:
            candidates = [item for item in ctx.evidence if item.id == hint]
            if not candidates:
                candidates = [
                    item for item in ctx.evidence if AssessmentOrchestrator._matches_evidence_hint(item, hint)
                ]
            for item in sorted(candidates, key=lambda evidence: evidence.confidence, reverse=True):
                if item.id not in seen_ids:
                    selected.append(item)
                    seen_ids.add(item.id)

        return selected or AssessmentOrchestrator._top_evidence(ctx.evidence, count=min(2, len(ctx.evidence)))

    @staticmethod
    def _top_evidence(evidence: list[EvidenceReference], count: int) -> list[EvidenceReference]:
        return sorted(evidence, key=lambda item: item.confidence, reverse=True)[:count]

    @staticmethod
    def _matches_evidence_hint(item: EvidenceReference, hint: str) -> bool:
        raw_text = f"{item.source_uri} {item.excerpt}".lower()
        collapsed_text = (
            raw_text.replace(" ", "")
            .replace("-", "")
            .replace("_", "")
            .replace("/", "")
            .replace(":", "")
        )
        cleaned_hint = hint.lower().removeprefix("ev-").replace("_", " ").replace("-", " ")
        tokens = [token for token in cleaned_hint.split() if token]
        if not tokens:
            return False

        collapsed_hint = "".join(tokens)
        if collapsed_hint and collapsed_hint in collapsed_text:
            return True

        return all(token in raw_text or token in collapsed_text for token in tokens[:2])
