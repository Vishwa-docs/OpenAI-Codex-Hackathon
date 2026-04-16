import { BulletList, ScenarioCards } from "@/components/section-page";
import { Card, SectionHeader } from "@/components/ui";
import { ScenarioComparison } from "@/components/visualizations";
import { loadProjectDataset } from "@/lib/app-api";

export default async function ScenariosPage({
  params
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  const project = await loadProjectDataset(projectId);

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Scenario analysis"
        title="What-if modeling for migration sequencing"
        description="Compare the trade-offs between security-first remediation, fast rehosting, and phased modernization."
      />
      <ScenarioComparison scenarios={project.scenarios} />
      <ScenarioCards scenarios={project.scenarios} />
      <div className="grid gap-4 xl:grid-cols-3">
        {project.roadmap.waves.map((wave) => (
          <Card key={wave.name} className="space-y-4">
            <div>
              <p className="text-xs uppercase tracking-[0.28em] text-slate-400">{wave.duration}</p>
              <h2 className="mt-2 text-lg font-medium text-white">{wave.name}</h2>
            </div>
            <p className="text-sm leading-6 text-slate-300">{wave.description}</p>
            <BulletList items={wave.exitCriteria} />
          </Card>
        ))}
      </div>
    </div>
  );
}
