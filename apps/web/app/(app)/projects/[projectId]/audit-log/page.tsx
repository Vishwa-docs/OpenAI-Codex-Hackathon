import { AuditTable } from "@/components/section-page";
import { SectionHeader } from "@/components/ui";
import { EvaluationPanel } from "@/components/visualizations";
import { loadProjectDataset } from "@/lib/app-api";

export default async function AuditLogPage({
  params
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  const project = await loadProjectDataset(projectId);

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Audit trail"
        title="Every key action is visible"
        description="Assessment starts, evidence normalization, recommendation aggregation, approvals, and exports all show up in the workspace audit log."
      />
      <AuditTable events={project.auditEvents} />
      <EvaluationPanel checks={project.evaluation.checks} overallScore={project.evaluation.overallScore} />
    </div>
  );
}
