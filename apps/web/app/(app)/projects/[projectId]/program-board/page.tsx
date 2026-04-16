import { ProgramBoardPanel } from "@/components/project-workspace";
import { SectionHeader } from "@/components/ui";
import { loadProjectDataset } from "@/lib/api";

export default async function ProgramBoardPage({
  params
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  const project = await loadProjectDataset(projectId);

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Program board"
        title="Pipeline and migration sequencing"
        description="Track the remediation, foundation, and cutover program in one place, with operator exit criteria and explicit control points."
      />
      <ProgramBoardPanel roadmap={project.roadmap} />
    </div>
  );
}
