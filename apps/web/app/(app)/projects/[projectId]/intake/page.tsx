import { BulletList } from "@/components/section-page";
import { Card, PillList, SectionHeader } from "@/components/ui";
import { loadProjectDataset } from "@/lib/app-api";

export default async function IntakePage({
  params
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  const project = await loadProjectDataset(projectId);

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Intake wizard"
        title="Structured migration intake"
        description="Capture business constraints, geography, compliance needs, and source connectivity before analysis begins."
      />
      <div className="grid gap-4 xl:grid-cols-3">
        <Card className="space-y-4">
          <h2 className="text-lg font-medium text-white">Business context</h2>
          <BulletList
            items={[
              project.overview.businessSummary,
              `Current phase: ${project.overview.phase}`,
              `Recommended provider: ${project.overview.recommendedProvider}`
            ]}
          />
        </Card>
        <Card className="space-y-4">
          <h2 className="text-lg font-medium text-white">Controls</h2>
          <PillList items={project.riskModel.complianceNotes} />
        </Card>
        <Card className="space-y-4">
          <h2 className="text-lg font-medium text-white">Execution posture</h2>
          <BulletList
            items={[
              "Read-only discovery by default",
              "Approval gate before planning artifacts become executable",
              "Connector credentials only required when a live integration is enabled"
            ]}
          />
        </Card>
      </div>
    </div>
  );
}
