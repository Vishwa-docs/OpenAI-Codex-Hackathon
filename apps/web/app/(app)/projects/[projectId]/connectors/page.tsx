import { Card, SectionHeader } from "@/components/ui";
import { loadProjectDataset } from "@/lib/api";

export default async function ConnectorsPage({
  params
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  const project = await loadProjectDataset(projectId);

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Connectors"
        title="Source, cloud, and factory integrations"
        description="The seeded demo works without external keys. Live connectors stay disabled or proposed until credentials and approvals are supplied."
      />
      <div className="grid gap-4 xl:grid-cols-2">
        {project.connectors.map((connector) => (
          <Card key={connector.id} className="space-y-3">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-[0.28em] text-slate-400">{connector.kind}</p>
                <h2 className="mt-2 text-lg font-medium text-white">{connector.name}</h2>
              </div>
              <span className="rounded-full bg-white/10 px-3 py-1 text-xs uppercase tracking-[0.2em] text-slate-200">
                {connector.status}
              </span>
            </div>
            <p className="text-sm leading-6 text-slate-300">{connector.details}</p>
            {connector.lastSyncAt ? (
              <p className="text-xs uppercase tracking-[0.22em] text-slate-400">Last sync {connector.lastSyncAt}</p>
            ) : null}
          </Card>
        ))}
      </div>
    </div>
  );
}
