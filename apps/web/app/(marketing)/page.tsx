import { Badge, Card, MetricCard } from "@/components/ui";
import { loadDashboardSummary, loadProjectDataset } from "@/lib/api";
import { formatConfidence, formatPercent } from "@/lib/format";
import Link from "next/link";

const pipelines = [
  {
    title: "A. Intake + connections",
    body: "Capture business context, compliance, regions, and source connectivity before any scan starts."
  },
  {
    title: "B. Evidence ingestion",
    body: "Normalize code, manifests, logs, Docker, CI/CD, and topology into a citation-ready dossier."
  },
  {
    title: "C. Assessment swarm",
    body: "Run specialist agents in parallel for discovery, infra, data, ops, security, risk, cloud, and cost."
  },
  {
    title: "D. Planning artifacts",
    body: "Generate diagrams, IaC snippets, migration waves, rollback plans, and operating checklists."
  },
  {
    title: "E. Report composition",
    body: "Produce executive, technical, cost, compliance, and roadmap packs from the same evidence base."
  },
  {
    title: "F. Evals + governance",
    body: "Score citation coverage, consistency, safety, and policy compliance before the recommendation is shown."
  }
];

const deliverables = [
  "Runnable local control plane with web, API, worker, PostgreSQL, Redis, and MinIO",
  "Marketing site and demo narrative that match the product’s operator workflow",
  "Seeded LegacyCart dossier with findings, scenarios, reports, artifacts, and approvals",
  "Agent Factory / Tool Factory proposals that stay disabled until approved"
];

export default async function MarketingHomePage() {
  const [dashboard, project] = await Promise.all([loadDashboardSummary(), loadProjectDataset("legacycart")]);

  return (
    <main className="mx-auto max-w-7xl px-6 pb-20 pt-14 lg:px-8">
      <section className="grid gap-8 lg:grid-cols-[1.25fr_0.75fr] lg:items-center">
        <div className="space-y-6">
          <Badge tone="blue">AI-native migration control plane</Badge>
          <div className="space-y-4">
            <h1 className="max-w-4xl text-5xl font-semibold tracking-tight text-white md:text-6xl">
              Turn legacy apps into evidence-backed cloud migration plans.
            </h1>
            <p className="max-w-2xl text-lg leading-8 text-slate-300">
              Cloud Migration Cockpit helps MSPs and consultancies assess readiness, compare providers, estimate ROI, and
              generate approval-ready migration artifacts from a single dashboard.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link
              href="/projects/legacycart"
              className="rounded-full bg-sky-400 px-6 py-3 text-sm font-medium text-slate-950 transition hover:bg-sky-300"
            >
              Open demo project
            </Link>
            <Link
              href="/product"
              className="rounded-full border border-white/15 px-6 py-3 text-sm font-medium text-white transition hover:bg-white/[0.08]"
            >
              See product tour
            </Link>
          </div>
          <div className="grid gap-4 pt-2 md:grid-cols-3">
            <MetricCard label="Active projects" value={`${dashboard.activeProjects}`} detail="Seeded portfolio view ready for investor demos." trend="+18%" />
            <MetricCard label="Pending approvals" value={`${dashboard.pendingApprovals}`} detail="Approval-gated planning keeps the execution phase safe." trend="2 locked" />
            <MetricCard label="Open findings" value={`${dashboard.openFindings}`} detail="All critical issues are cited back to evidence and files." trend="4 critical" />
          </div>
        </div>
        <Card className="space-y-4 border-sky-400/20 bg-sky-400/[0.06]">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Seeded project</p>
              <h2 className="mt-2 text-2xl font-semibold text-white">{project.projectName}</h2>
            </div>
            <Badge tone="amber">{formatPercent(project.overview.readinessScore)}</Badge>
          </div>
          <p className="text-sm leading-6 text-slate-300">{project.overview.narrative}</p>
          <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-4">
            <p className="text-xs uppercase tracking-[0.25em] text-slate-400">Recommendation</p>
            <p className="mt-2 text-lg font-medium text-white">{project.overview.migrationDecision}</p>
            <p className="mt-2 text-sm text-slate-300">{formatConfidence(project.overview.confidence)}</p>
          </div>
          <div className="space-y-3 text-sm text-slate-300">
            {project.reportHighlights.map((item) => (
              <div key={item} className="rounded-2xl bg-white/5 px-4 py-3 leading-6">
                {item}
              </div>
            ))}
          </div>
        </Card>
      </section>

      <section className="mt-12 grid gap-4 lg:grid-cols-4">
        <Card>
          <p className="text-sm uppercase tracking-[0.24em] text-slate-400">Assessment</p>
          <p className="mt-3 text-2xl font-semibold text-white">Evidence first</p>
          <p className="mt-2 text-sm leading-6 text-slate-300">Every recommendation stays tied to files, logs, manifests, and graph edges.</p>
        </Card>
        <Card>
          <p className="text-sm uppercase tracking-[0.24em] text-slate-400">Planning</p>
          <p className="mt-3 text-2xl font-semibold text-white">Phase approved</p>
          <p className="mt-2 text-sm leading-6 text-slate-300">Migration waves, rollback plans, and artifacts are only exposed after approval gates.</p>
        </Card>
        <Card>
          <p className="text-sm uppercase tracking-[0.24em] text-slate-400">Execution</p>
          <p className="mt-3 text-2xl font-semibold text-white">AWS-first ready</p>
          <p className="mt-2 text-sm leading-6 text-slate-300">The shell is already shaped for a future dry-run-first cloud execution layer.</p>
        </Card>
        <Card>
          <p className="text-sm uppercase tracking-[0.24em] text-slate-400">Evals</p>
          <p className="mt-3 text-2xl font-semibold text-white">{project.evaluation.overallScore}/100</p>
          <p className="mt-2 text-sm leading-6 text-slate-300">Report completeness, citation coverage, and safety checks are scored in-product.</p>
        </Card>
      </section>

      <section className="mt-14 grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
        <Card className="space-y-4">
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Why it feels different</p>
          <h2 className="text-3xl font-semibold text-white">Built as a control plane, not a calculator.</h2>
          <p className="max-w-3xl text-sm leading-7 text-slate-300">
            The product keeps executive framing and operator evidence in the same project space. Leaders see readiness,
            risk, cost, and approvals first. Architects can immediately drill into citations, graph edges, agent runs,
            and report sections without switching tools.
          </p>
          <div className="grid gap-3 md:grid-cols-2">
            {deliverables.map((item) => (
              <div key={item} className="rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-4 text-sm leading-6 text-slate-300">
                {item}
              </div>
            ))}
          </div>
        </Card>
        <Card className="space-y-4 border-emerald-400/20 bg-emerald-400/[0.05]">
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Local product</p>
          <h2 className="text-3xl font-semibold text-white">Run the entire cockpit on your laptop.</h2>
          <p className="text-sm leading-7 text-slate-300">
            `make stack` launches the marketing site, cockpit UI, FastAPI control plane, worker service, PostgreSQL,
            Redis, and MinIO. The demo is self-contained, but the connector surfaces are ready for live credentials when
            you want them.
          </p>
          <div className="rounded-3xl border border-white/10 bg-slate-950/40 p-4 font-mono text-sm text-sky-100">
            npm install
            <br />
            uv sync
            <br />
            make stack
          </div>
        </Card>
      </section>

      <section className="mt-14">
        <div className="mb-6 flex items-end justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Pipeline model</p>
            <h2 className="mt-2 text-3xl font-semibold text-white">Six explicit pipelines, one evidence backbone.</h2>
          </div>
          <Link href="/product" className="text-sm font-medium text-sky-200 transition hover:text-sky-100">
            View the product story
          </Link>
        </div>
        <div className="grid gap-4 lg:grid-cols-3">
          {pipelines.map((pipeline) => (
            <Card key={pipeline.title} className="space-y-3">
              <h3 className="text-lg font-medium text-white">{pipeline.title}</h3>
              <p className="text-sm leading-6 text-slate-300">{pipeline.body}</p>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}
