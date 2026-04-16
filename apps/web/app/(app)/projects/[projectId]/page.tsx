import {
  CommandCenterPanel,
  DeploymentReadinessPanel,
  ExecutiveRibbon,
  MtcPipelinePanel,
  ObservabilityPanel,
  OperatorWorkspacePanel,
  ProgramBoardPanel,
  ReportCenterPanel
} from "@/components/project-workspace";
import { RecommendationList } from "@/components/section-page";
import { Card, MetricCard, PillList, SectionHeader } from "@/components/ui";
import { EvaluationPanel, ProviderComparison, ReadinessGauge } from "@/components/visualizations";
import { loadProjectDataset } from "@/lib/api";
import { formatConfidence } from "@/lib/format";

export default async function ProjectOverviewPage({
  params
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  const project = await loadProjectDataset(projectId);

  return (
    <div className="space-y-6">
      <ExecutiveRibbon
        overview={project.overview}
        costModel={project.costModel}
        riskModel={project.riskModel}
        approvals={project.approvals}
      />
      <SectionHeader
        eyebrow="Project overview"
        title="Migration readiness, evidence posture, and operator context"
        description={project.overview.narrative}
      />
      <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <ReadinessGauge
          readiness={project.overview.readinessScore}
          confidence={project.overview.confidence}
          decision={project.overview.migrationDecision}
        />
        <Card className="space-y-4">
          <h2 className="text-lg font-medium text-white">Program snapshot</h2>
          <div className="grid gap-3 md:grid-cols-2">
            <MetricCard label="Phase" value={project.overview.phase} detail="Current workflow phase in the seeded program." />
            <MetricCard label="Status" value={project.overview.status} detail="Human approval and execution posture." />
          </div>
          <div className="space-y-3 text-sm leading-6 text-slate-300">
            <p>Client: {project.clientName}</p>
            <p>Source: {project.overview.sourceSystem}</p>
            <p>Target: {project.overview.targetSystem}</p>
            <p>{formatConfidence(project.overview.confidence)}</p>
          </div>
          <PillList items={project.reportHighlights} />
        </Card>
      </div>
      <OperatorWorkspacePanel
        findings={project.findings}
        recommendations={project.recommendations}
        agentRuns={project.agentRuns}
        scenarioDiffs={project.scenarioDiffs}
      />
      <ProgramBoardPanel roadmap={project.roadmap} />
      <MtcPipelinePanel mtcPipeline={project.mtcPipeline} />
      <ObservabilityPanel observability={project.observability} />
      <DeploymentReadinessPanel deploymentPlan={project.deploymentPlan} />
      <CommandCenterPanel
        connectors={project.connectors}
        approvals={project.approvals}
        auditEvents={project.auditEvents}
        evaluation={project.evaluation}
      />
      <ReportCenterPanel
        artifacts={project.artifacts}
        reports={project.reports}
        exportFormats={project.exportFormats}
      />
      <RecommendationList recommendations={project.recommendations} />
      <ProviderComparison providers={project.providers} />
      <EvaluationPanel checks={project.evaluation.checks} overallScore={project.evaluation.overallScore} />
    </div>
  );
}
