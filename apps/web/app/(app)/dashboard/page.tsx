import { Card, MetricCard, SectionHeader } from "@/components/ui";
import { loadDashboardSummary } from "@/lib/app-api";
import Link from "next/link";

export default async function DashboardPage() {
  const dashboard = await loadDashboardSummary();

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Dashboard"
        title="Your migration portfolio at a glance"
        description="Track readiness, approvals, findings, and report output without leaving the cockpit."
      />
      <div className="grid gap-4 xl:grid-cols-4">
        <MetricCard label="Active projects" value={`${dashboard.activeProjects}`} detail="Active client workspaces and projects in the portfolio." />
        <MetricCard label="Pending approvals" value={`${dashboard.pendingApprovals}`} detail="Planning gates keep execution controlled." />
        <MetricCard label="Open findings" value={`${dashboard.openFindings}`} detail="Critical blockers are evidence-linked." />
        <MetricCard label="Report exports" value={`${dashboard.reportExports}`} detail="Executive and technical outputs are ready to ship." trend="+7 today" />
      </div>
      <Card className="space-y-4">
        <h2 className="text-lg font-medium text-white">Priority projects</h2>
        <div className="grid gap-4 lg:grid-cols-3">
          {dashboard.topProjects.map((project) => (
            <Link
              key={project.id}
              href={`/projects/${project.id}`}
              className="rounded-3xl border border-white/10 bg-white/5 p-4 transition hover:bg-white/10"
            >
              <p className="text-xs uppercase tracking-[0.25em] text-slate-400">{project.clientName}</p>
              <h3 className="mt-2 text-lg font-medium text-white">{project.name}</h3>
              <p className="mt-3 text-sm text-slate-300">{project.migrationDecision}</p>
              <div className="mt-4 flex items-center justify-between text-sm text-slate-300">
                <span>{project.phase}</span>
                <span>{project.recommendedProvider}</span>
              </div>
            </Link>
          ))}
        </div>
      </Card>
    </div>
  );
}
