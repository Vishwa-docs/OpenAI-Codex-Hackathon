import { EvidenceList } from "@/components/section-page";
import { Card, SectionHeader } from "@/components/ui";
import { DependencyGraph } from "@/components/visualizations";
import { loadProjectDataset } from "@/lib/api";

export default async function DependenciesPage({
  params
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  const project = await loadProjectDataset(projectId);

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Dependency graph"
        title="Legacy topology and evidence graph"
        description="The cockpit normalizes service, job, database, storage, and integration dependencies before recommending a migration path."
      />
      <DependencyGraph nodes={project.dependencyNodes} edges={project.dependencyEdges} />
      <Card className="space-y-3">
        <h2 className="text-lg font-medium text-white">Observed graph traits</h2>
        <div className="space-y-2 text-sm leading-6 text-slate-300">
          <p>{project.dependencyNodes.length} normalized nodes across app, data, storage, delivery, and integration surfaces.</p>
          <p>{project.dependencyEdges.length} graph edges tie findings back to concrete dependencies and deployment behavior.</p>
          <p>The first MVP keeps this graph read-only so the assessment remains stable and explainable.</p>
        </div>
      </Card>
      <EvidenceList evidence={project.evidence.slice(0, 6)} />
    </div>
  );
}
