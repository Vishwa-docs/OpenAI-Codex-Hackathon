import { BulletList } from "@/components/section-page";
import { Card, SectionHeader } from "@/components/ui";
import { loadProjectDataset } from "@/lib/app-api";

export default async function ProjectSettingsPage({
  params
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  const project = await loadProjectDataset(projectId);

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Project settings"
        title="Governance and execution defaults"
        description="Defaults stay safe: discovery is read-only, write actions are disabled, and approvals are explicit."
      />
      <div className="grid gap-4 xl:grid-cols-2">
        <Card className="space-y-4">
          <h2 className="text-lg font-medium text-white">Current posture</h2>
          <BulletList
            items={[
              `Project status: ${project.overview.status}`,
              `Recommended provider: ${project.overview.recommendedProvider}`,
              "Execution adapters remain disabled until approval"
            ]}
          />
        </Card>
        <Card className="space-y-4">
          <h2 className="text-lg font-medium text-white">Approval prerequisites</h2>
          <BulletList items={project.roadmap.cutover} />
        </Card>
      </div>
    </div>
  );
}
