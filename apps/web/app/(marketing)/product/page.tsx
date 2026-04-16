import { Card, SectionHeader } from "@/components/ui";
import Link from "next/link";

const features = [
  {
    title: "Assessment cockpit",
    body: "Analyze codebases, manifests, logs, and dependency graphs with evidence-backed recommendations."
  },
  {
    title: "Planning artifacts",
    body: "Generate diagrams, IaC snippets, cutover steps, and rollback notes once planning is approved."
  },
  {
    title: "Factory layer",
    body: "Detect tool gaps, scaffold disabled connector stubs, and track prompt/tool versioning."
  }
];

const outputSets = [
  "Executive summary for non-technical stakeholders",
  "Technical migration dossier with evidence-backed findings",
  "Provider comparison, scenario diffs, and cost / ROI framing",
  "Architecture diagrams, Terraform snippets, and migration wave plans",
  "Approval records, audit trail, and eval scorecards",
  "Factory proposals for missing tools and connectors"
];

const surfaces = [
  "Executive ribbon with readiness, confidence, risk, and approval state",
  "Operator workspace with citations, agent runs, and scenario comparisons",
  "Command Center for pipeline health, connector status, and policy warnings",
  "Report Center with previews, version history, and PDF export",
  "Artifacts space for diagrams, IaC, rollback plans, and checklists"
];

export default function ProductPage() {
  return (
    <main className="mx-auto max-w-7xl px-6 pb-20 pt-14 lg:px-8">
      <SectionHeader
        eyebrow="Product"
        title="A migration control plane that reads like a board deck and behaves like an engineering system."
        description="The first slice prioritizes speed, clarity, and evidence so the cockpit is useful in both sales demos and real assessments."
        action={
          <Link href="/projects/legacycart" className="rounded-full bg-sky-400 px-5 py-3 text-sm font-medium text-slate-950">
            Open cockpit
          </Link>
        }
      />
      <div className="mt-8 grid gap-4 lg:grid-cols-3">
        {features.map((feature) => (
          <Card key={feature.title} className="space-y-3">
            <h2 className="text-lg font-medium text-white">{feature.title}</h2>
            <p className="text-sm leading-6 text-slate-300">{feature.body}</p>
          </Card>
        ))}
      </div>
      <div className="mt-8 grid gap-4 lg:grid-cols-[1fr_1fr]">
        <Card className="space-y-4">
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">What ships</p>
          <h2 className="text-2xl font-semibold text-white">A real project dossier, not a shallow summary.</h2>
          <div className="grid gap-3">
            {outputSets.map((item) => (
              <div key={item} className="rounded-2xl bg-white/5 px-4 py-3 text-sm leading-6 text-slate-300">
                {item}
              </div>
            ))}
          </div>
        </Card>
        <Card className="space-y-4">
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">How teams use it</p>
          <h2 className="text-2xl font-semibold text-white">One shell for stakeholders and operators.</h2>
          <div className="grid gap-3">
            {surfaces.map((item) => (
              <div key={item} className="rounded-2xl bg-white/5 px-4 py-3 text-sm leading-6 text-slate-300">
                {item}
              </div>
            ))}
          </div>
        </Card>
      </div>
      <Card className="mt-8 space-y-3">
        <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Designed for</p>
        <p className="text-2xl font-semibold text-white">MSPs, solution architects, CTOs, and cloud operators</p>
        <p className="max-w-3xl text-sm leading-6 text-slate-300">
          The shell balances executive visibility and technical depth: one project dossier, one evidence trail, multiple
          views depending on who is in the room.
        </p>
      </Card>
    </main>
  );
}
