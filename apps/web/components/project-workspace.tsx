import type {
  ApprovalRecord,
  AgentRun,
  AuditEvent,
  Report,
  ReportArtifact,
  ScenarioDiff
} from "@contracts/index";
import { Badge, Card, MetricCard, PillList } from "@/components/ui";
import { formatConfidence, formatDateTime, formatPercent } from "@/lib/format";
import type { ConnectorItem, EvalSummary, ProjectDataset } from "@/lib/project-dataset";

export function ExecutiveRibbon({
  overview,
  costModel,
  riskModel,
  approvals
}: {
  overview: ProjectDataset["overview"];
  costModel: ProjectDataset["costModel"];
  riskModel: ProjectDataset["riskModel"];
  approvals: ApprovalRecord[];
}) {
  const approvalState =
    approvals.find((approval) => approval.phase.toLowerCase().includes("planning"))?.state ?? "pending";

  return (
    <Card className="space-y-5 border-sky-400/20 bg-[linear-gradient(135deg,rgba(56,189,248,0.16),rgba(15,23,42,0.92))]">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
        <div className="max-w-3xl">
          <p className="text-xs uppercase tracking-[0.3em] text-sky-100/75">Executive ribbon</p>
          <h2 className="mt-2 text-3xl font-semibold text-white">{overview.migrationDecision}</h2>
          <p className="mt-2 text-sm leading-6 text-slate-200">
            {overview.narrative}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge tone="amber">{formatPercent(overview.readinessScore)} readiness</Badge>
          <Badge tone="blue">{overview.recommendedProvider}</Badge>
          <Badge tone={approvalState === "approved" ? "green" : "amber"}>{approvalState}</Badge>
        </div>
      </div>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-6">
        <MetricCard label="Readiness" value={formatPercent(overview.readinessScore)} detail="Migration readiness score" />
        <MetricCard label="Migration decision" value="Deferred" detail="Current control-plane recommendation" />
        <MetricCard label="Confidence" value={formatConfidence(overview.confidence)} detail="Confidence after critic review" />
        <MetricCard label="Cost delta" value={`$${(costModel.currentMonthlyRunRate - costModel.targetMonthlyRunRate).toLocaleString()}/mo`} detail="Run-rate reduction after migration" />
        <MetricCard label="Risk level" value={riskModel.overallRisk} detail="Current stakeholder-facing risk posture" />
        <MetricCard label="Approval state" value={approvalState} detail="Planning approval controls execution readiness" />
      </div>
    </Card>
  );
}

export function OperatorWorkspacePanel({
  findings,
  recommendations,
  agentRuns,
  scenarioDiffs
}: {
  findings: ProjectDataset["findings"];
  recommendations: ProjectDataset["recommendations"];
  agentRuns: AgentRun[];
  scenarioDiffs: ScenarioDiff[];
}) {
  return (
    <Card className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Operator workspace</p>
          <h3 className="mt-2 text-xl font-medium text-white">Evidence and actioning surface</h3>
        </div>
        <Badge tone="blue">{findings.length} findings</Badge>
      </div>
      <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="space-y-3">
          {recommendations.slice(0, 2).map((recommendation) => (
            <div key={recommendation.id} className="rounded-3xl bg-white/5 p-4">
              <div className="flex items-start justify-between gap-4">
                <h4 className="text-base font-medium text-white">{recommendation.title}</h4>
                <Badge tone={recommendation.impact === "high" ? "green" : "amber"}>{recommendation.impact}</Badge>
              </div>
              <p className="mt-2 text-sm leading-6 text-slate-300">{recommendation.summary}</p>
            </div>
          ))}
        </div>
        <div className="space-y-3">
          <div className="rounded-3xl bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Agent run timeline</p>
            <div className="mt-3 space-y-3">
              {agentRuns.slice(0, 3).map((run) => (
                <div key={run.id} className="rounded-2xl border border-white/8 p-3">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-sm font-medium text-white">{run.displayName}</span>
                    <Badge tone={run.critic ? "amber" : "slate"}>{run.stage}</Badge>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-slate-300">{run.summary}</p>
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-3xl bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Scenario diff</p>
            <div className="mt-3 space-y-3">
              {scenarioDiffs.map((diff) => (
                <div key={diff.comparedScenarioId} className="rounded-2xl border border-white/8 p-3">
                  <p className="text-sm font-medium text-white">{diff.summary}</p>
                  <p className="mt-2 text-sm leading-6 text-slate-300">{diff.riskShift}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}

export function ProgramBoardPanel({ roadmap }: { roadmap: ProjectDataset["roadmap"] }) {
  return (
    <Card className="space-y-4">
      <div>
        <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Program board</p>
        <h3 className="mt-2 text-xl font-medium text-white">Pipeline and migration sequencing</h3>
      </div>
      <div className="grid gap-3 xl:grid-cols-3">
        {roadmap.waves.map((wave) => (
          <div key={wave.name} className="rounded-3xl bg-white/5 p-4">
            <div className="flex items-center justify-between gap-3">
              <h4 className="text-base font-medium text-white">{wave.name}</h4>
              <Badge tone="blue">{wave.duration}</Badge>
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-300">{wave.description}</p>
            <div className="mt-3">
              <PillList items={wave.exitCriteria} />
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

export function CommandCenterPanel({
  connectors,
  approvals,
  auditEvents,
  evaluation
}: {
  connectors: ConnectorItem[];
  approvals: ApprovalRecord[];
  auditEvents: AuditEvent[];
  evaluation: EvalSummary;
}) {
  return (
    <Card className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Command center</p>
          <h3 className="mt-2 text-xl font-medium text-white">Pipelines, connectors, and governance</h3>
        </div>
        <Badge tone={evaluation.overallScore >= 90 ? "green" : "amber"}>{evaluation.overallScore}/100</Badge>
      </div>
      <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="space-y-3">
          <div className="rounded-3xl bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Connector health</p>
            <div className="mt-3 space-y-3">
              {connectors.slice(0, 4).map((connector) => (
                <div key={connector.id} className="flex items-start justify-between gap-3 rounded-2xl border border-white/8 p-3">
                  <div>
                    <p className="text-sm font-medium text-white">{connector.name}</p>
                    <p className="mt-1 text-sm text-slate-300">{connector.details}</p>
                  </div>
                  <Badge
                    tone={
                      connector.status === "connected"
                        ? "green"
                        : connector.status === "proposed" || connector.status === "needs_configuration"
                          ? "amber"
                          : "slate"
                    }
                  >
                    {connector.status}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-3xl bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Approval queue</p>
            <div className="mt-3 space-y-3">
              {approvals.map((approval) => (
                <div key={approval.id} className="rounded-2xl border border-white/8 p-3">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-sm font-medium text-white">{approval.phase}</span>
                    <Badge tone={approval.state === "approved" ? "green" : approval.state === "pending" ? "amber" : "slate"}>
                      {approval.state}
                    </Badge>
                  </div>
                  {approval.comment ? <p className="mt-2 text-sm text-slate-300">{approval.comment}</p> : null}
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="rounded-3xl bg-white/5 p-4">
          <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Recent audit activity</p>
          <div className="mt-3 space-y-3">
            {auditEvents.slice(0, 4).map((event) => (
              <div key={event.id} className="rounded-2xl border border-white/8 p-3">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-sm font-medium text-white">{event.action}</span>
                  <span className="text-xs uppercase tracking-[0.22em] text-slate-400">{formatDateTime(event.createdAt)}</span>
                </div>
                <p className="mt-2 text-sm text-slate-300">
                  {event.actor} updated {event.entityType} `{event.entityId}`.
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Card>
  );
}

export function ReportCenterPanel({
  artifacts,
  reports,
  exportFormats
}: {
  artifacts: ReportArtifact[];
  reports: Report[];
  exportFormats: string[];
}) {
  return (
    <Card className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Report center</p>
          <h3 className="mt-2 text-xl font-medium text-white">Report previews and export paths</h3>
        </div>
        <Badge tone="blue">{reports.length} reports</Badge>
      </div>
      <div className="grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="space-y-3">
          {artifacts.slice(0, 3).map((artifact) => (
            <div key={artifact.id} className="rounded-3xl bg-white/5 p-4">
              <div className="flex items-center justify-between gap-3">
                <h4 className="text-base font-medium text-white">{artifact.title}</h4>
                <Badge tone="slate">{artifact.format}</Badge>
              </div>
              <p className="mt-2 text-sm leading-6 text-slate-300">{artifact.description}</p>
            </div>
          ))}
        </div>
        <div className="space-y-3">
          <div className="rounded-3xl bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Highlighted exports</p>
            <div className="mt-3">
              <PillList items={exportFormats} />
            </div>
          </div>
          <div className="rounded-3xl bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Narrative previews</p>
            <div className="mt-3 space-y-3">
              {reports.slice(0, 3).map((report) => (
                <div key={report.id} className="rounded-2xl border border-white/8 p-3">
                  <p className="text-sm font-medium text-white">{report.title}</p>
                  <p className="mt-2 text-sm leading-6 text-slate-300">{report.summary}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}
