import { ApprovalActionCards } from "@/components/approval-action-cards";
import { BulletList } from "@/components/section-page";
import { Card, SectionHeader } from "@/components/ui";
import { loadProjectDataset } from "@/lib/app-api";

export default async function ApprovalsPage({
  params
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  const project = await loadProjectDataset(projectId);

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Approval center"
        title="Human-in-the-loop control points"
        description="Planning and execution remain gated. Proposed tools and connectors stay disabled until they are explicitly approved."
      />
      <ApprovalActionCards projectId={project.projectId} approvals={project.approvals} />
      <Card className="space-y-4">
        <h2 className="text-lg font-medium text-white">Proposed factory entries</h2>
        <BulletList
          items={project.connectors
            .filter((connector) => connector.status === "proposed" || connector.status === "disabled")
            .map((connector) => `${connector.name}: ${connector.details}`)}
        />
      </Card>
    </div>
  );
}
