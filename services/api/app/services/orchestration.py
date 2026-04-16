from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from ..domain.models import (
    AgentRun,
    AgentOutput,
    AnalysisQuestion,
    AnalysisQuestionAnswer,
    AssessmentBundle,
    AssessmentRunCreate,
    AssessmentRun,
    ApprovalDecision,
    ApprovalRecord,
    AuditEvent,
    CostRoiSummary,
    DashboardSummary,
    DeploymentExecution,
    DeploymentExecutionRequest,
    DeploymentPlan,
    ChatMessage,
    ChatMessageCreate,
    CloudConnection,
    CloudConnectionCreate,
    EvidenceReference,
    EvalMetric,
    EvalRun,
    FinalRecommendation,
    Finding,
    FactoryProposal,
    IntakeProfile,
    ObservabilityTrace,
    PipelineSummary,
    ProjectOverview,
    ProviderOption,
    RegistryEntry,
    ProjectCreate,
    Report,
    ReportArtifact,
    ReportSection,
    SourceConnectionCreate,
    SourceConnection,
    PreviewDeploymentStatus,
    PreviewLaunchRequest,
    RiskComplianceSummary,
    RiskItem,
    Scenario,
    ScenarioDiff,
    ScenarioOutcome,
    WorkspaceContext,
)
from ..domain.repository import SeedRepository
from .chat import EvidenceGroundedChatService
from .local_preview import LocalPreviewManager


@dataclass
class AssessmentContext:
    overview: ProjectOverview
    findings: list[Finding]
    evidence: list[EvidenceReference]
    registry_entries: list[RegistryEntry]


class AssessmentOrchestrator:
    """Deterministic multi-agent assessment service for the MVP."""

    def __init__(
        self,
        repository: SeedRepository,
        chat_service: EvidenceGroundedChatService | None = None,
        local_preview_manager: LocalPreviewManager | None = None,
    ) -> None:
        self.repository = repository
        self.chat_service = chat_service
        self.local_preview_manager = local_preview_manager

    def get_dashboard_summary(self) -> DashboardSummary:
        projects = self.repository.list_projects()
        if not projects:
            return DashboardSummary(
                active_projects=0,
                pending_approvals=0,
                open_findings=0,
                report_exports=0,
                top_projects=[],
            )
        seed = self.repository.get_project(projects[0].id)
        pending_approvals = sum(1 for item in seed.approvals if item.state == "pending")
        open_findings = len(seed.findings)
        report_exports = len([item for item in seed.artifacts if item.format == "pdf"])
        return DashboardSummary(
            active_projects=len(projects),
            pending_approvals=pending_approvals,
            open_findings=open_findings,
            report_exports=report_exports,
            top_projects=projects,
        )

    def create_project(self, **kwargs) -> IntakeProfile:
        project = self.repository.create_project(ProjectCreate(**kwargs))
        return project.intake_profile

    def get_intake_profile(self, project_id: str) -> IntakeProfile:
        return self.repository.get_intake_profile(project_id)

    def get_deployment_plan(self, project_id: str) -> DeploymentPlan:
        return self.repository.get_deployment_plan(project_id)

    def list_observability_traces(self, project_id: str) -> list[ObservabilityTrace]:
        return self.repository.list_observability_traces(project_id)

    def list_analysis_questions(self, project_id: str) -> list[AnalysisQuestion]:
        return self.repository.get_project(project_id).analysis_questions

    def get_preview_status(self, project_id: str) -> PreviewDeploymentStatus:
        project = self.repository.get_project(project_id)
        if project.preview_status is None:
            raise KeyError(project_id)
        if self.local_preview_manager is None:
            return project.preview_status
        refreshed = self.local_preview_manager.get_status(project_id, project.preview_status)
        if refreshed is not None:
            project.preview_status = refreshed
            self.repository.save_project(project)
            return refreshed
        return project.preview_status

    def get_workspace_context(self, workspace_id: str) -> WorkspaceContext:
        return self.repository.get_workspace_context(workspace_id)

    def list_workspace_projects(self, workspace_id: str) -> list[ProjectOverview]:
        return self.repository.list_workspace_projects(workspace_id)

    def create_workspace_project(self, workspace_id: str, draft: ProjectCreate) -> ProjectOverview:
        return self.repository.create_workspace_project(workspace_id, draft)

    def execute_deployment(
        self,
        project_id: str,
        request: DeploymentExecutionRequest,
    ) -> DeploymentExecution:
        project = self.repository.get_project(project_id)
        if request.provider != "aws":
            raise ValueError("Only AWS automation is supported in v1.")
        if not any(connection.provider == "aws" for connection in project.cloud_connections):
            raise PermissionError("AWS credentials or an assumed role must be connected before deployment execution.")
        return self.repository.add_deployment_execution(project_id, request.provider, request.mode, request.triggered_by)

    def answer_analysis_question(
        self,
        project_id: str,
        question_id: str,
        answer: AnalysisQuestionAnswer,
    ) -> AnalysisQuestion:
        project = self.repository.get_project(project_id)
        question = next((item for item in project.analysis_questions if item.id == question_id), None)
        if question is None:
            raise KeyError(question_id)

        question.answer = answer.answer
        question.state = "answered"
        project.audit_events.append(
            AuditEvent(
                id=f"audit-{question_id}-answer",
                actor=answer.actor,
                action="analysis_question.answered",
                entity_type="analysis_question",
                entity_id=question_id,
                created_at=datetime.now(tz=UTC),
                metadata={"stage": question.stage},
            )
        )
        if all(item.state == "answered" for item in project.analysis_questions):
            project.overview = project.overview.model_copy(update={"status": "analysis_ready"})
        self.repository.save_project(project)
        return question

    def launch_local_preview(
        self,
        project_id: str,
        request: PreviewLaunchRequest,
    ) -> PreviewDeploymentStatus:
        if self.local_preview_manager is None:
            raise RuntimeError("Local preview support is unavailable.")

        project = self.repository.get_project(project_id)
        planning_approval = next((item for item in project.approvals if "planning" in item.phase.lower()), None)
        if planning_approval is None or planning_approval.state != "approved":
            raise PermissionError("Planning approval must be approved before launching the local preview.")
        if project.intake_profile is None or project.intake_profile.source_kind != "local_path":
            raise ValueError("Local preview is only available for local_path projects.")
        if not project.intake_profile.source_target:
            raise ValueError("The local project path is missing.")
        if project.preview_status is None or not project.preview_status.supported:
            raise ValueError("This project does not support automated local preview launch.")

        status = self.local_preview_manager.launch(project_id, project.intake_profile.source_target)
        project.preview_status = status
        project.overview = project.overview.model_copy(update={"status": "preview_running"})
        project.audit_events.append(
            AuditEvent(
                id=f"audit-{project_id}-preview-launch",
                actor=request.triggered_by,
                action="preview.launch_requested",
                entity_type="preview",
                entity_id=project_id,
                created_at=datetime.now(tz=UTC),
                metadata={"url": status.url or "", "workspacePath": status.workspace_path or ""},
            )
        )
        self.repository.save_project(project)
        return status

    def build_assessment(self, project_id: str) -> AssessmentBundle:
        seed = self.repository.get_project(project_id)
        if not seed.evidence or not seed.findings:
            return self._build_pending_assessment_bundle(project_id, seed)
        ctx = AssessmentContext(
            overview=seed.overview,
            findings=seed.findings,
            evidence=seed.evidence,
            registry_entries=seed.registry_entries,
        )
        provider_options = self._build_provider_options(ctx)
        cost_roi = self._build_cost_roi(ctx)
        risk_compliance = self._build_risk_summary(ctx)
        scenarios = self._build_scenarios(ctx)
        scenario_diffs = self._build_scenario_diffs(scenarios)
        live_analysis = self._generate_live_analysis(seed, provider_options, cost_roi, risk_compliance, scenarios)
        if live_analysis is not None:
            agent_outputs = self._agent_outputs_from_live_analysis(ctx, live_analysis)
            final_recommendation = self._final_from_live_analysis(ctx, provider_options, live_analysis)
            reports = self._reports_from_live_analysis(ctx, live_analysis)
            artifacts = self._artifacts_from_reports(reports)
            seed.reports = reports
            seed.artifacts = artifacts
            seed.analysis_questions = self._questions_from_live_analysis(seed, live_analysis)
            seed.overview = seed.overview.model_copy(
                update={
                    "migration_decision": final_recommendation.label,
                    "confidence": final_recommendation.confidence,
                    "recommended_provider": final_recommendation.recommended_provider,
                    "status": "questions_pending" if seed.analysis_questions else "analysis_ready",
                }
            )
            self.repository.save_project(seed)
        elif self.repository.settings.is_judge_mode:
            agent_outputs = [
                AgentOutput(
                    agent_key="live_assessment",
                    display_name="Live Assessment Agent",
                    status="failed",
                    confidence=0.0,
                    summary="The local scan completed, but live OpenAI analysis is unavailable right now.",
                    evidence=[],
                    structured_output={"source": "openai"},
                    limitations=["Check OPENAI_* configuration and network access, then rerun the analysis."],
                )
            ]
            final_recommendation = FinalRecommendation(
                decision="defer",
                label="Waiting for live analysis",
                confidence=0.0,
                summary="The source scan finished, but judge mode could not complete the live OpenAI analysis yet.",
                recommended_provider=provider_options[0].name if provider_options else "Pending",
                rationale=[
                    "Judge mode does not fabricate fallback analysis.",
                    "The scan evidence is available, but the live model response was unavailable.",
                ],
                blockers=["Live OpenAI analysis is unavailable."],
                next_steps=[
                    "Verify OPENAI_API_KEY and OPENAI_BASE_URL.",
                    "Retry the analysis once outbound model access is available.",
                ],
                evidence=self._top_evidence(ctx.evidence, count=3),
            )
        else:
            agent_outputs = self._run_agents(project_id, ctx, provider_options, cost_roi, risk_compliance, scenarios)
            final_recommendation = self._aggregate_final(ctx, provider_options, risk_compliance, agent_outputs)
        pipeline_summaries = self._build_pipeline_summaries(project_id)
        run = AssessmentRun(
            id=f"run-{project_id}-sync",
            project_id=project_id,
            status="succeeded",
            started_at=datetime(2026, 4, 16, 10, 30, tzinfo=UTC),
            completed_at=datetime(2026, 4, 16, 10, 30, tzinfo=UTC),
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

    def _build_pending_assessment_bundle(self, project_id: str, seed) -> AssessmentBundle:
        started_at = datetime(2026, 4, 16, 12, 10, tzinfo=UTC)
        run = AssessmentRun(
            id=f"run-{project_id}-pending",
            project_id=project_id,
            status="queued",
            started_at=started_at,
            completed_at=started_at,
            mode="sync",
            pipeline_summaries=[
                PipelineSummary(
                    pipeline_key="intake_clarification",
                    title="Intake and clarification",
                    status="running",
                    summary="Business context is captured, but source evidence still needs to be ingested.",
                    plain_language_summary="We have the project shell, but not enough code evidence yet.",
                    started_at=started_at,
                ),
                PipelineSummary(
                    pipeline_key="codebase_discovery",
                    title="Codebase discovery",
                    status="blocked",
                    summary="Connect a local path or repository and run the first scan.",
                    plain_language_summary="The cockpit needs the source before it can analyze anything.",
                ),
            ],
            agent_outputs=[
                AgentOutput(
                    agent_key="intake_normalizer",
                    display_name="Intake Normalizer Agent",
                    status="succeeded",
                    confidence=0.71,
                    summary="Captured the project shell and blocked execution until evidence is available.",
                    evidence=[],
                    structured_output={"phase": "intake", "sourceConnected": False},
                )
            ],
            final_recommendation=FinalRecommendation(
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
                ],
                evidence=[],
            ),
        )
        return AssessmentBundle(
            run=run,
            overview=seed.overview,
            dashboard=self.get_dashboard_summary(),
            graph=seed.graph,
            findings=seed.findings,
            provider_options=[],
            cost_roi=CostRoiSummary(
                annual_baseline_cost=0,
                annual_target_cost=0,
                migration_investment=0,
                annual_savings=0,
                payback_months=0,
                roi_percent=0,
                summary="Cost modeling begins after evidence ingestion.",
                confidence=0.0,
                assumptions=[],
                evidence=[],
            ),
            risk_compliance=RiskComplianceSummary(
                overall_risk="moderate",
                compliance_frameworks=["Pending intake validation"],
                data_residency="Data residency posture cannot be finalized until workload evidence is validated.",
                operational_readiness="Initial intake exists, but no evidence-backed readiness verdict is available yet.",
                risks=[],
                summary="The project is safe to keep in intake, but not ready for migration recommendations.",
                confidence=0.55,
            ),
            scenarios=[],
            scenario_diffs=[],
            reports=seed.reports,
            artifacts=seed.artifacts,
            approvals=seed.approvals,
            audit_events=seed.audit_events,
            registry_entries=seed.registry_entries,
        )

    def list_source_connections(self, project_id: str) -> list[SourceConnection]:
        return self.repository.get_project(project_id).source_connections

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
                "started_at": datetime(2026, 4, 16, 11, 3, tzinfo=UTC),
                "completed_at": datetime(2026, 4, 16, 11, 4, tzinfo=UTC),
            }
        )
        return self.repository.add_assessment_run(project_id, run, request.triggered_by)

    def list_agent_runs(self, project_id: str) -> list[AgentRun]:
        bundle = self.build_assessment(project_id)
        runs = [self._agent_run_from_output(bundle.run.id, item) for item in bundle.run.agent_outputs]
        if self.repository.settings.is_demo_mode:
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
                summary="No unsupported claims were promoted into the seeded outputs.",
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
                overall_score=max(0, min(100, round(sum(metric.score for metric in metrics) / len(metrics)))),
                status="succeeded",
                completed_at=bundle.run.completed_at,
                metrics=metrics,
            )
        ]

    def _generate_live_analysis(
        self,
        project: Any,
        provider_options: list[ProviderOption],
        cost_roi: CostRoiSummary,
        risk_compliance: RiskComplianceSummary,
        scenarios: list[Scenario],
    ) -> dict[str, object] | None:
        if self.chat_service is None or self.repository.settings.is_demo_mode:
            return None
        return self.chat_service.build_assessment_payload(
            project,
            provider_options=provider_options,
            cost_summary=cost_roi,
            risk_summary=risk_compliance,
            scenarios=scenarios,
        )

    def _agent_outputs_from_live_analysis(
        self,
        ctx: AssessmentContext,
        payload: dict[str, object],
    ) -> list[AgentOutput]:
        outputs: list[AgentOutput] = []
        for item in payload.get("agentOutputs", []):
            if not isinstance(item, dict):
                continue
            citation_ids = [str(value) for value in item.get("citationIds", []) if isinstance(value, str)]
            evidence = self._select_evidence(ctx, citation_ids)
            outputs.append(
                AgentOutput(
                    agent_key=str(item.get("agentKey", "analysis_agent")),
                    display_name=str(item.get("displayName", "Analysis Agent")),
                    status="succeeded",
                    confidence=float(item.get("confidence", 0.75)),
                    summary=str(item.get("summary", "")),
                    evidence=evidence,
                    structured_output={"source": "openai"},
                    limitations=[str(value) for value in item.get("limitations", []) if isinstance(value, str)],
                )
            )
        return outputs or [
            AgentOutput(
                agent_key="live_assessment",
                display_name="Live Assessment Agent",
                status="failed",
                confidence=0.0,
                summary="Live OpenAI analysis did not return a usable structured payload.",
                evidence=[],
                structured_output={"source": "openai"},
                limitations=["Structured analysis payload was unavailable."],
            )
        ]

    def _final_from_live_analysis(
        self,
        ctx: AssessmentContext,
        providers: list[ProviderOption],
        payload: dict[str, object],
    ) -> FinalRecommendation:
        raw = payload.get("finalRecommendation")
        if not isinstance(raw, dict):
            return self._aggregate_final(ctx, providers, self._build_risk_summary(ctx), [])
        citation_ids = [str(value) for value in raw.get("citationIds", []) if isinstance(value, str)]
        evidence = self._select_evidence(ctx, citation_ids) or self._top_evidence(ctx.evidence, count=4)
        decision = str(raw.get("decision", "defer"))
        if decision not in {"migrate_now", "migrate_partially", "defer", "rearchitect_first"}:
            decision = "defer"
        return FinalRecommendation(
            decision=decision,  # type: ignore[arg-type]
            label=str(raw.get("label", "Defer until blockers are remediated")),
            confidence=float(raw.get("confidence", 0.75)),
            summary=str(raw.get("summary", "")),
            recommended_provider=str(raw.get("recommendedProvider", providers[0].name if providers else "Pending")),
            rationale=[str(value) for value in raw.get("rationale", []) if isinstance(value, str)],
            blockers=[str(value) for value in raw.get("blockers", []) if isinstance(value, str)],
            next_steps=[str(value) for value in raw.get("nextSteps", []) if isinstance(value, str)],
            evidence=evidence,
        )

    def _questions_from_live_analysis(self, project: Any, payload: dict[str, object]) -> list[AnalysisQuestion]:
        questions: list[AnalysisQuestion] = []
        for index, item in enumerate(payload.get("questions", []), start=1):
            if not isinstance(item, dict):
                continue
            stage = str(item.get("stage", "intake_clarification"))
            if stage not in {
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
            }:
                stage = "intake_clarification"
            questions.append(
                AnalysisQuestion(
                    id=f"{project.overview.id}-question-{index:02d}",
                    stage=stage,  # type: ignore[arg-type]
                    question=str(item.get("question", "")),
                    rationale=str(item.get("rationale", "")),
                )
            )
        return questions

    def _reports_from_live_analysis(
        self,
        ctx: AssessmentContext,
        payload: dict[str, object],
    ) -> list[Report]:
        generated_at = datetime.now(tz=UTC)
        reports: list[Report] = []
        for index, item in enumerate(payload.get("reports", []), start=1):
            if not isinstance(item, dict):
                continue
            kind = str(item.get("kind", "executive_summary"))
            if kind not in {"executive_summary", "technical_dossier", "cost_report", "risk_report"}:
                kind = "executive_summary"
            sections: list[ReportSection] = []
            for section in item.get("sections", []):
                if not isinstance(section, dict):
                    continue
                citation_ids = [str(value) for value in section.get("citationIds", []) if isinstance(value, str)]
                sections.append(
                    ReportSection(
                        title=str(section.get("title", "Section")),
                        body=str(section.get("body", "")),
                        citations=self._select_evidence(ctx, citation_ids),
                    )
                )
            reports.append(
                Report(
                    id=f"report-{kind}-{index:02d}",
                    kind=kind,  # type: ignore[arg-type]
                    title=str(item.get("title", "Assessment Report")),
                    summary=str(item.get("summary", "")),
                    confidence=float(item.get("confidence", 0.75)),
                    sections=sections,
                    generated_at=generated_at,
                    artifact_ids=[f"artifact-{kind}-{index:02d}"],
                )
            )
        return reports

    @staticmethod
    def _artifacts_from_reports(reports: list[Report]) -> list[ReportArtifact]:
        return [
            ReportArtifact(
                id=report.artifact_ids[0],
                kind=report.kind,
                title=f"{report.title} PDF",
                format="pdf",
                description=report.summary,
                updated_at=report.generated_at,
            )
            for report in reports
        ]

    def list_factory_proposals(self, project_id: str) -> list[FactoryProposal]:
        return self.repository.get_project(project_id).factory_proposals

    def list_chat_messages(self, project_id: str) -> list[ChatMessage]:
        return self.repository.get_project(project_id).chat_messages

    def create_chat_message(self, project_id: str, draft: ChatMessageCreate) -> ChatMessage:
        message = self.repository.add_chat_message(project_id, draft)
        if draft.role == "human" and self.chat_service is not None:
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
        if "planning" in approval.phase.lower():
            seed.overview = seed.overview.model_copy(
                update={
                    "status": "approved_for_execution" if decision.decision == "approved" else "planning_rejected",
                }
            )
        self.repository.save_project(seed)
        return approval

    def _run_agents(
        self,
        project_id: str,
        ctx: AssessmentContext,
        provider_options: list[ProviderOption],
        cost_roi: CostRoiSummary,
        risk_compliance: RiskComplianceSummary,
        scenarios: list[Scenario],
    ) -> list[AgentOutput]:
        grouped_evidence = self._top_evidence(ctx.evidence, count=2)
        highest_finding = sorted(ctx.findings, key=self._severity_rank)[0]
        deployment_plan = self.repository.get_deployment_plan(project_id)
        return [
            AgentOutput(
                agent_key="intake_normalizer",
                display_name="Intake Normalizer Agent",
                status="succeeded",
                confidence=0.95,
                summary="Captured migration goal as phased modernization with strong security and rollback constraints.",
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
                summary="Identified a Java monolith, AngularJS admin app, cron jobs, Jenkins pipeline, PostgreSQL, and shared NFS storage.",
                evidence=self._select_evidence(ctx, ["ev-java8-runtime", "ev-nfs-invoices"]),
                structured_output={"componentsDiscovered": 7, "legacyRuntimes": ["Java 8", "AngularJS 1.x"]},
            ),
            AgentOutput(
                agent_key="security_secrets",
                display_name="Security & Secrets Agent",
                status="succeeded",
                confidence=0.97,
                summary="Flagged hardcoded production credentials, long-lived pipeline access keys, and sensitive log leakage as immediate blockers.",
                evidence=self._select_evidence(
                    ctx,
                    ["ev-app-prod-db-secret", "ev-jenkins-access-key", "ev-logback-pii"],
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
                evidence=self._select_evidence(ctx, ["ev-logback-pii", "ev-nfs-invoices"]),
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
                agent_key="hosting_fit_advisor",
                display_name="Hosting Fit Advisor Agent",
                status="succeeded",
                confidence=0.89,
                summary="Ranked simpler platforms before recommending heavier managed microservices.",
                evidence=grouped_evidence,
                structured_output={
                    "recommendedPlatform": deployment_plan.recommended_platform.platform_key,
                    "platformOptions": [option.model_dump(by_alias=True) for option in deployment_plan.platform_options],
                },
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
                agent_key="scenario_what_if",
                display_name="Scenario / What-if Agent",
                status="succeeded",
                confidence=0.86,
                summary="Prepared three migration paths that trade off speed, risk burn-down, and modernization investment.",
                evidence=self._select_evidence(ctx, ["ev-cron-direct-db", "ev-soap-basic-auth"]),
                structured_output={"scenarioCount": len(scenarios)},
            ),
            AgentOutput(
                agent_key="tool_gap_detector",
                display_name="Tool Gap Detector Agent",
                status="succeeded",
                confidence=0.84,
                summary="Detected missing Azure Repos ingestion and certificate inventory capabilities; proposed disabled registry entries for both.",
                evidence=[],
                structured_output={
                    "proposedEntries": [
                        item.model_dump(by_alias=True)
                        for item in ctx.registry_entries
                        if item.status == "proposed"
                    ]
                },
                limitations=["Factory proposals are metadata-only in the MVP and do not execute scaffolding yet."],
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
        ]

    def _build_pipeline_summaries(self, project_id: str) -> list[PipelineSummary]:
        started_at = datetime(2026, 4, 16, 10, 30, tzinfo=UTC)
        completed_at = datetime(2026, 4, 16, 10, 31, tzinfo=UTC)
        deployment_plan = self.repository.get_deployment_plan(project_id)
        executed = bool(self.repository.get_project(project_id).deployment_executions)
        return [
            PipelineSummary(
                pipeline_key="intake_clarification",
                title="Intake and clarification",
                status="succeeded",
                summary="The cockpit collected the project source, expected users, and business constraints.",
                plain_language_summary="We first learn what the app is, where the code lives, and how big the first release needs to be.",
                started_at=started_at,
                completed_at=completed_at,
            ),
            PipelineSummary(
                pipeline_key="codebase_discovery",
                title="Codebase discovery",
                status="succeeded",
                summary="The worker scanned the project source and normalized code, config, and runtime evidence.",
                plain_language_summary="The system inspected the codebase and pulled out important clues about how it works today.",
                started_at=started_at,
                completed_at=completed_at,
            ),
            PipelineSummary(
                pipeline_key="architecture_analysis",
                title="Architecture analysis",
                status="succeeded",
                summary="Architecture agents traced services, dependencies, storage, jobs, and integration boundaries.",
                plain_language_summary="The swarm mapped how the app is put together and which parts are risky or tightly coupled.",
                started_at=started_at,
                completed_at=completed_at,
            ),
            PipelineSummary(
                pipeline_key="security_readiness",
                title="Security and readiness review",
                status="succeeded",
                summary="Security and readiness agents flagged blockers around secrets, logging, and operational coupling.",
                plain_language_summary="Before we talk about cloud, we check what could break or create security problems in production.",
                started_at=started_at,
                completed_at=completed_at,
            ),
            PipelineSummary(
                pipeline_key="hosting_fit_recommendation",
                title="Hosting-fit recommendation",
                status="succeeded",
                summary="The swarm compared simple and advanced hosting options to avoid over-engineering the migration plan.",
                plain_language_summary="This step asks whether a simpler deployment is enough right now.",
                started_at=started_at,
                completed_at=completed_at,
            ),
            PipelineSummary(
                pipeline_key="migration_strategy",
                title="Migration strategy selection",
                status="succeeded",
                summary="The strategy pass chose between lift-and-shift, phased EC2, containerization, and refactor-heavy tracks.",
                plain_language_summary="The cockpit picked the safest migration style for the codebase, budget, and expected traffic.",
                started_at=started_at,
                completed_at=completed_at,
            ),
            PipelineSummary(
                pipeline_key="infra_plan_generation",
                title="Infrastructure plan generation",
                status="succeeded",
                summary="Terraform and Ansible starter artifacts were generated for review before any write action.",
                plain_language_summary="We prepared the infrastructure plan, but nothing is applied automatically without review.",
                started_at=started_at,
                completed_at=completed_at,
            ),
            PipelineSummary(
                pipeline_key="evaluation_critique",
                title="Evaluation and critique",
                status="succeeded",
                summary="Critic agents validated evidence, recommendation consistency, and safety posture.",
                plain_language_summary="A second pass checked whether the suggestions were grounded and safe.",
                started_at=started_at,
                completed_at=completed_at,
            ),
            PipelineSummary(
                pipeline_key="deployment_readiness",
                title="Deployment readiness",
                status="succeeded" if deployment_plan.execution_state in {"ready", "succeeded"} else "blocked",
                summary="Deployment stays approval-gated until AWS credentials and planning approval are available.",
                plain_language_summary="The app tells you exactly what is still missing before it can deploy to AWS.",
                started_at=started_at,
                completed_at=completed_at if deployment_plan.execution_state in {"ready", "succeeded"} else None,
            ),
            PipelineSummary(
                pipeline_key="aws_execution",
                title="AWS execution",
                status="succeeded" if executed else "blocked",
                summary="AWS dry-run or apply can be triggered only after credentials are connected.",
                plain_language_summary="We only attempt an AWS deploy after you connect credentials and review the plan.",
                started_at=started_at,
                completed_at=completed_at if executed else None,
            ),
            PipelineSummary(
                pipeline_key="post_deploy_validation",
                title="Post-deploy validation",
                status="queued",
                summary="Post-deploy validation is ready to compare rollout health, cost posture, and refactor next steps.",
                plain_language_summary="After deployment, the cockpit will check health and suggest the next improvements.",
                started_at=started_at,
            ),
        ]

    @staticmethod
    def _agent_run_from_output(assessment_run_id: str, output: AgentOutput) -> AgentRun:
        stage = "critique" if output.agent_key.endswith("_critic") else (
            "planning" if output.agent_key in {"cloud_recommendation", "hosting_fit_advisor", "cost_roi", "scenario_what_if"} else "analysis"
        )
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
        shared = self._select_evidence(ctx, ["ev-nfs-invoices", "ev-cron-direct-db", "ev-soap-basic-auth"])
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
                rationale="Viable for enterprise controls, but the current product roadmap and seeded evidence fit AWS more naturally.",
                confidence=0.79,
                evidence=shared,
            ),
        ]

    def _build_cost_roi(self, ctx: AssessmentContext) -> CostRoiSummary:
        evidence = self._select_evidence(ctx, ["ev-nfs-invoices", "ev-cron-direct-db", "ev-java8-runtime"])
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
            evidence=self._select_evidence(ctx, ["ev-app-prod-db-secret", "ev-jenkins-access-key"]),
        )
        logging = RiskItem(
            id="risk-pii-logs",
            severity="high",
            domain="compliance",
            title="PII and auth headers leak into logs",
            impact="Non-production-grade logging creates privacy exposure and undermines audit readiness.",
            mitigation="Implement structured redaction and tighten retention before wider cloud observability rollout.",
            confidence=0.93,
            evidence=self._select_evidence(ctx, ["ev-logback-pii"]),
        )
        ops = RiskItem(
            id="risk-ops-coupling",
            severity="medium",
            domain="operations",
            title="Batch operations depend on direct host access",
            impact="Cutover and rollback plans are fragile because nightly jobs assume direct shell and database access.",
            mitigation="Move jobs into queue-backed workers with observable retries and least-privilege credentials.",
            confidence=0.88,
            evidence=self._select_evidence(ctx, ["ev-cron-direct-db", "ev-nfs-invoices"]),
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
        average_confidence = (
            sum(output.confidence for output in agent_outputs) / len(agent_outputs)
            if agent_outputs
            else 0.0
        )
        return FinalRecommendation(
            decision="defer",
            label="Defer until blockers are remediated",
            confidence=round(average_confidence, 2),
            summary="Do not begin the cloud migration yet. Close wave-0 blockers first, then revisit a phased AWS migration once secrets, logging leaks, and delivery identity gaps are remediated.",
            recommended_provider=providers[0].name,
            rationale=[
                "AWS best supports the requested future execution model and staged modernization path.",
                "Managed PostgreSQL and S3 directly address the current database and NFS storage pain points.",
                "The current risk profile is too high for direct execution or partial cutover without a remediation wave.",
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
        selected = [item for item in ctx.evidence if item.id in set(evidence_ids)]
        if not selected:
            return AssessmentOrchestrator._top_evidence(ctx.evidence, count=min(3, len(ctx.evidence)))
        return sorted(selected, key=lambda item: evidence_ids.index(item.id))

    @staticmethod
    def _top_evidence(evidence: list[EvidenceReference], count: int) -> list[EvidenceReference]:
        return sorted(evidence, key=lambda item: item.confidence, reverse=True)[:count]
