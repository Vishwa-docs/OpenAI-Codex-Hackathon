import { FindingsList, RecommendationList } from "@/components/section-page";
import { SectionHeader } from "@/components/ui";
import { loadProjectDataset } from "@/lib/app-api";

export default async function FindingsPage({
  params
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  const project = await loadProjectDataset(projectId);

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Findings"
        title="Evidence-backed blockers and remediation guidance"
        description="Every blocker ties back to concrete evidence, confidence, and a recommended mitigation path."
      />
      <FindingsList findings={project.findings} />
      <RecommendationList recommendations={project.recommendations} />
    </div>
  );
}
