import { Card, SectionHeader } from "@/components/ui";
import { loadProjectDataset } from "@/lib/api";

export default async function SettingsPage() {
  const project = await loadProjectDataset("legacycart");

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Settings"
        title="Workspace settings and connector posture"
        description="The MVP is read-only by default. Cloud execution and external connectors remain disabled until they are explicitly approved."
      />
      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="space-y-3">
          <h2 className="text-lg font-medium text-white">Connector defaults</h2>
          <div className="space-y-2 text-sm text-slate-300">
            <p>Local directories: enabled for seeded demos</p>
            <p>GitHub: connector scaffold available, disabled until credentials are supplied</p>
            <p>Azure Repos: connector scaffold available, disabled until credentials are supplied</p>
            <p>AWS execution adapter: locked until planning approval</p>
          </div>
        </Card>
        <Card className="space-y-3">
          <h2 className="text-lg font-medium text-white">Evaluation summary</h2>
          <div className="space-y-2 text-sm text-slate-300">
            {project.evaluation.checks.map((check) => (
              <div key={check.name} className="rounded-2xl bg-white/5 px-4 py-3">
                <div className="flex items-center justify-between gap-3">
                  <span className="font-medium text-white">{check.name}</span>
                  <span>{check.score}</span>
                </div>
                <p className="mt-1 leading-6">{check.note}</p>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
