import { CommandCenterPanel } from "@/components/project-workspace";
import { SectionHeader } from "@/components/ui";
import { loadProjectDataset } from "@/lib/api";

export default async function CommandCenterPage({
  params
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  const project = await loadProjectDataset(projectId);

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Command center"
        title="Connectors, approvals, and recent control-plane activity"
        description="Operational view over pipeline health, approval posture, connector state, and the latest audit events."
      />
      <CommandCenterPanel
        connectors={project.connectors}
        approvals={project.approvals}
        auditEvents={project.auditEvents}
        evaluation={project.evaluation}
      />
    </div>
  );
}
