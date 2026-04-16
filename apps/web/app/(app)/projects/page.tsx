import { Card, SectionHeader } from "@/components/ui";
import { DEFAULT_WORKSPACE_ID, loadWorkspaceProjects } from "@/lib/app-api";
import { formatConfidence, formatPercent } from "@/lib/format";
import Link from "next/link";

export default async function ProjectsPage() {
  const projects = await loadWorkspaceProjects(DEFAULT_WORKSPACE_ID);

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Projects"
        title="Migration projects and client workspaces"
        description="Open an existing workspace, review portfolio health, or start a new intake with the same cockpit workflow."
        action={
          <Link
            href="/projects/new"
            className="rounded-full bg-sky-400 px-5 py-2.5 text-sm font-medium text-slate-950 transition hover:bg-sky-300"
          >
            New project
          </Link>
        }
      />
      {projects.length === 0 ? (
        <Card className="space-y-4">
          <h2 className="text-lg font-medium text-white">No projects yet</h2>
          <p className="text-sm leading-6 text-slate-300">
            The judge workspace starts empty. Create a project from a real local path or repository URL to begin the agentic analysis.
          </p>
          <div>
            <Link
              href="/projects/new"
              className="inline-flex rounded-full bg-sky-400 px-5 py-2.5 text-sm font-medium text-slate-950 transition hover:bg-sky-300"
            >
              Start the first analysis
            </Link>
          </div>
        </Card>
      ) : (
        <div className="grid gap-4 xl:grid-cols-3">
        {projects.map((project) => (
          <Link key={project.id} href={`/projects/${project.id}`}>
            <Card className="h-full space-y-4 transition hover:bg-white/[0.08]">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs uppercase tracking-[0.28em] text-slate-400">{project.clientName}</p>
                  <h2 className="mt-2 text-lg font-medium text-white">{project.name}</h2>
                </div>
                <span className="rounded-full bg-sky-400/15 px-3 py-1 text-xs font-medium text-sky-100">
                  {formatPercent(project.readinessScore)}
                </span>
              </div>
              <p className="text-sm leading-6 text-slate-300">{project.migrationDecision}</p>
              <div className="space-y-2 text-sm text-slate-300">
                <div>Phase: {project.phase}</div>
                <div>Status: {project.status}</div>
                <div>Provider: {project.recommendedProvider}</div>
                <div>{formatConfidence(project.confidence)}</div>
              </div>
            </Card>
          </Link>
        ))}
        </div>
      )}
    </div>
  );
}
