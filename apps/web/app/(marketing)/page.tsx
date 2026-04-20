import { Badge } from "@/components/ui";
import { DEFAULT_WORKSPACE_ID, loadRuntimeHealth, loadWorkspaceContext } from "@/lib/app-api";
import { getDesktopDownloadUrl } from "@/lib/runtime";
import Link from "next/link";

const operatingRails = [
  {
    title: "Source intake",
    body: "Bring in a repo, local directory, or demo seed with explicit connection posture and branch context."
  },
  {
    title: "Evidence model",
    body: "Normalize files, manifests, jobs, logs, and runtime signals into one citation-ready assessment bundle."
  },
  {
    title: "Assessment swarm",
    body: "Score risk, provider fit, cost, and sequencing with specialist agents that surface assumptions and confidence."
  },
  {
    title: "Approval handoff",
    body: "Hand technical evidence into reports, approvals, and planning artifacts without losing the operator trail."
  }
];

const deliverables = [
  "Runnable local control plane with web, API, worker, and SQLite-backed persistence",
  "Marketing site and judge workflow that match the product's operator experience",
  "Empty intake workspace that starts from a real local path instead of a seeded project",
  "Agent Factory / Tool Factory proposals that stay disabled until approved"
];

const operatingModel = [
  {
    label: "Sell",
    title: "The SaaS site explains the platform like a product, not a setup guide.",
    body: "This surface positions the product, frames the workflow, and helps buyers understand why the system matters."
  },
  {
    label: "Run",
    title: "The AI executes locally where code, evidence, and credentials already live.",
    body: "Assessment runs, evidence gathering, and report assembly stay close to the actual working environment instead of pretending everything happens in the browser."
  },
  {
    label: "Operate",
    title: "The dashboard becomes the single interaction layer for the MTC pipeline.",
    body: "Questions, inferences, reports, approvals, and drill-down views all meet in one workspace after the run starts."
  }
];

const outcomes = [
  {
    label: "For MSP teams",
    title: "Show executives a clean decision, not a wall of scanner output.",
    body: "The public-facing story is business-readable while the cockpit still holds the full technical trace."
  },
  {
    label: "For solution architects",
    title: "Stay close to the graph, the findings, and the run history.",
    body: "You can move from recommendation to cited files, dependency edges, approvals, and report artifacts in one surface."
  },
  {
    label: "For demos",
    title: "Run a believable workflow in minutes.",
    body: "Download the macOS app, paste a real local path, and open the cockpit on a live analysis state."
  }
];

const proof = [
  "Judge workspace starts empty and waits for a real local source path",
  "Hosted-style SaaS story plus operator cockpit in one Next.js app",
  "Local worker, API, approvals, reports, artifacts, and evaluation surfaces",
  "Packaged macOS launcher that starts the local stack and opens the intake workflow"
];

export default async function MarketingHomePage() {
  const [runtimeHealth, workspace] = await Promise.all([
    loadRuntimeHealth().catch(() => null),
    loadWorkspaceContext(DEFAULT_WORKSPACE_ID).catch(() => null),
  ]);

  return (
    <main className="overflow-hidden pb-24">
      <section className="relative border-b border-white/10 px-6 pb-20 pt-16 lg:px-8 lg:pb-28 lg:pt-24">
        <div className="mx-auto grid max-w-7xl gap-14 lg:grid-cols-[1.1fr_0.9fr] lg:items-end">
          <div>
            <Badge tone="blue">Product-led SaaS surface</Badge>
            <div className="mt-8 space-y-6">
              <p className="text-sm uppercase tracking-[0.32em] text-sky-200/80">Cloud Migration Cockpit</p>
              <h1 className="max-w-4xl text-5xl font-semibold tracking-tight text-white md:text-6xl lg:text-7xl">
                Sell the platform in public. Run the migration workflow in the dashboard.
              </h1>
              <p className="max-w-2xl text-lg leading-8 text-slate-300">
                Cloud Migration Cockpit gives you a polished public product story, then hands real work to a local AI
                runtime and an operator dashboard built for questions, inferences, reports, and approvals.
              </p>
            </div>

            <div className="mt-10 flex flex-wrap gap-3">
              <Link
                href={getDesktopDownloadUrl()}
                className="rounded-full bg-sky-400 px-6 py-3 text-sm font-medium text-slate-950 transition hover:bg-sky-300"
              >
                Download macOS app
              </Link>
              <Link
                href="/projects/new"
                className="rounded-full border border-white/10 px-6 py-3 text-sm font-medium text-white transition hover:bg-white/[0.06]"
              >
                Open intake workspace
              </Link>
            </div>

            <div className="mt-12 grid gap-6 border-t border-white/10 pt-8 md:grid-cols-3">
              <div>
                <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Decision quality</p>
                <p className="mt-3 text-3xl font-semibold text-white">Evidence first</p>
                <p className="mt-2 text-sm leading-6 text-slate-300">
                  Findings, recommendations, and reports stay tied back to files, manifests, and operational context.
                </p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Program safety</p>
                <p className="mt-3 text-3xl font-semibold text-white">Approval gated</p>
                <p className="mt-2 text-sm leading-6 text-slate-300">
                  Planning surfaces can move fast without quietly crossing into destructive execution.
                </p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Demo speed</p>
                <p className="mt-3 text-3xl font-semibold text-white">One workflow</p>
                <p className="mt-2 text-sm leading-6 text-slate-300">
                  Launch the packaged app, paste a real local project path, and hand off into the cockpit without demo scaffolding.
                </p>
              </div>
            </div>
          </div>
          <div className="relative min-h-[560px] overflow-hidden rounded-[2rem] border border-white/10 bg-[linear-gradient(160deg,rgba(10,19,32,0.94),rgba(7,17,29,0.82))] p-6 shadow-glow">
            <div className="absolute inset-x-8 top-10 h-px bg-gradient-to-r from-transparent via-sky-300/60 to-transparent" />
            <div className="grid gap-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Operating model</p>
                  <h2 className="mt-3 text-2xl font-semibold text-white">
                    The public story, the local AI, and the dashboard each do one job well.
                  </h2>
                </div>
                <span className="inline-flex items-center rounded-2xl border border-sky-300/15 bg-sky-400/8 px-4 py-2 text-[11px] font-medium tracking-[0.18em] text-sky-100/90">
                  SaaS + local AI + dashboard
                </span>
              </div>

              <div className="grid gap-4">
                {operatingRails.map((rail, index) => (
                  <div key={rail.title} className="grid gap-3 rounded-[1.7rem] border border-white/10 bg-white/[0.04] p-4 md:grid-cols-[18px_1fr]">
                    <p className="pt-2 text-xs uppercase tracking-[0.28em] text-slate-400">{`0${index + 1}`}</p>
                    <div>
                      <h3 className="text-lg font-medium text-white">{rail.title}</h3>
                      <p className="mt-2 text-sm leading-6 text-slate-300">{rail.body}</p>
                    </div>
                  </div>
                ))}
              </div>

              <div className="grid gap-4 border-t border-white/10 pt-4 md:grid-cols-2">
                {proof.map((item) => (
                  <p key={item} className="text-sm leading-6 text-slate-300">
                    {item}
                  </p>
                ))}
              </div>
              <div className="rounded-[1.6rem] border border-white/10 bg-slate-950/35 p-4">
                <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Runtime status</p>
                <div className="mt-3 grid gap-3 md:grid-cols-2">
                  <div>
                    <p className="text-sm font-medium text-white">{runtimeHealth?.service ?? "Local runtime not started yet"}</p>
                    <p className="mt-2 text-sm leading-6 text-slate-300">
                      {runtimeHealth
                        ? `Mode ${runtimeHealth.appMode} · version ${runtimeHealth.version} · workspace ${runtimeHealth.defaultWorkspaceId}`
                        : "Launch the local stack or the desktop app to publish live runtime metadata here."}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-white">
                      {runtimeHealth?.desktopAvailable ? "Desktop package ready" : "Desktop package needs a fresh build"}
                    </p>
                    <p className="mt-2 text-sm leading-6 text-slate-300">
                      {workspace
                        ? `${workspace.workspace.projectCount} active judge projects in the local workspace.`
                        : "Workspace availability will appear here as soon as the control plane is reachable."}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto mt-16 max-w-7xl px-6 lg:px-8">
        <div className="grid gap-10 lg:grid-cols-[0.85fr_1.15fr]">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Why this split matters</p>
            <h2 className="mt-4 text-4xl font-semibold text-white">The homepage sells clarity. The dashboard carries the work.</h2>
          </div>
          <div className="grid gap-5">
            {outcomes.map((item) => (
              <div key={item.title} className="border-b border-white/10 pb-5 last:border-b-0 last:pb-0">
                <p className="text-xs uppercase tracking-[0.28em] text-sky-200/80">{item.label}</p>
                <h3 className="mt-3 text-2xl font-medium text-white">{item.title}</h3>
                <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-300">{item.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto mt-16 max-w-7xl px-6 lg:px-8">
        <div className="grid gap-6 lg:grid-cols-3">
          {operatingModel.map((item) => (
            <div key={item.label} className="border-t border-white/10 pt-5">
              <p className="text-xs uppercase tracking-[0.28em] text-sky-200/80">{item.label}</p>
              <h3 className="mt-3 text-2xl font-medium text-white">{item.title}</h3>
              <p className="mt-3 text-sm leading-7 text-slate-300">{item.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto mt-16 max-w-7xl px-6 lg:px-8">
        <div className="overflow-hidden rounded-[2.4rem] border border-white/10 bg-white/[0.04] p-8 lg:p-10">
          <div className="grid gap-8 lg:grid-cols-[0.9fr_1.1fr] lg:items-end">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Interactive demo</p>
              <h2 className="mt-4 text-4xl font-semibold text-white">
                Use the packaged desktop app to move from download to a real local-path analysis.
              </h2>
              <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-300">
                The judge workflow is intentionally direct. Download the macOS app, launch the judge workspace, paste a
                real local project path, and let the swarm produce questions, reports, approvals, and the local preview handoff.
              </p>
              <div className="mt-6 grid gap-3">
                {deliverables.slice(0, 2).map((item) => (
                  <div key={item} className="rounded-[1.5rem] border border-white/10 bg-white/[0.04] px-4 py-3 text-sm leading-6 text-slate-300">
                    {item}
                  </div>
                ))}
              </div>
            </div>
            <div className="flex flex-wrap gap-3 lg:justify-end">
              <Link
                href={getDesktopDownloadUrl()}
                className="rounded-full bg-white px-6 py-3 text-sm font-medium text-slate-950 transition hover:bg-slate-200"
              >
                Download launcher
              </Link>
              <Link
                href="/projects/new"
                className="rounded-full border border-white/10 px-6 py-3 text-sm font-medium text-white transition hover:bg-white/[0.06]"
              >
                Open judge intake
              </Link>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}

