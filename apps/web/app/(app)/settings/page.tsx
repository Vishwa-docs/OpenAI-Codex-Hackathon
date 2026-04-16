import { Card, SectionHeader } from "@/components/ui";
import { DEFAULT_WORKSPACE_ID, loadWorkspaceContext } from "@/lib/app-api";

export default async function SettingsPage() {
  const context = await loadWorkspaceContext(DEFAULT_WORKSPACE_ID);

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Settings"
        title="Workspace settings and connector posture"
        description="The workspace is read-only by default. Cloud execution and external connectors remain disabled until they are explicitly approved."
      />
      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="space-y-3">
          <h2 className="text-lg font-medium text-white">Workspace posture</h2>
          <div className="space-y-2 text-sm text-slate-300">
            <p>Organization: {context.organization.name}</p>
            <p>Workspace: {context.workspace.name}</p>
            <p>Mode: {context.workspace.mode}</p>
            <p>Projects in scope: {context.workspace.projectCount}</p>
          </div>
        </Card>
        <Card className="space-y-3">
          <h2 className="text-lg font-medium text-white">Client accounts</h2>
          <div className="space-y-2 text-sm text-slate-300">
            {context.clientAccounts.map((account) => (
              <div key={account.id} className="rounded-2xl bg-white/5 px-4 py-3">
                <div className="flex items-center justify-between gap-3">
                  <span className="font-medium text-white">{account.name}</span>
                  <span>{account.primaryRegion}</span>
                </div>
                <p className="mt-1 leading-6">
                  {account.industry} · {account.complianceTags.join(", ") || "No compliance tags yet"}
                </p>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
