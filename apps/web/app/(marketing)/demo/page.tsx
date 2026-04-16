import { BackendUnavailableError, loadProjectDataset } from "@/lib/api";
import { createMockProjectDataset } from "@/lib/mock-data";
import { DemoWorkflowForm } from "@/components/demo-workflow-form";
import { Badge, SectionHeader } from "@/components/ui";
import { getDesktopDownloadUrl, isJudgeMode } from "@/lib/runtime";
import Link from "next/link";

const stages = [
  {
    title: "Paste target repo",
    body: "Use any GitHub repository URL you control. The workflow normalizes the branch target before it starts.",
  },
  {
    title: "Seed LegacyCart",
    body: "We package the bundled MTC dummy project into a temporary git workspace so the target repo gets believable content.",
  },
  {
    title: "Push or simulate",
    body: "Leave the token blank to run a safe simulation, or add one to perform the live branch push.",
  },
  {
    title: "Open cockpit",
    body: "The workflow registers the source connection and queues a local-worker assessment so the cockpit has fresh activity.",
  },
];

const checklist = [
  "GitHub URL",
  "Optional PAT for live branch push",
  "Seeded LegacyCart project bundled in the repo",
  "Automatic source registration and assessment kickoff",
];

export default async function DemoPage() {
  if (isJudgeMode()) {
    return (
      <main className="mx-auto max-w-7xl px-6 pb-20 pt-14 lg:px-8">
        <div className="grid gap-10 lg:grid-cols-[1fr_0.95fr]">
          <div>
            <SectionHeader
              eyebrow="Judge workflow"
              title="Judge mode disables the seeded demo and starts from the packaged desktop app."
              description="The localhost workflow now begins with a download, an empty intake workspace, and a real local project path. No LegacyCart seed or simulated fallback is used in this mode."
              action={
                <Link href={getDesktopDownloadUrl()} className="rounded-full bg-sky-400 px-5 py-3 text-sm font-medium text-slate-950">
                  Download macOS app
                </Link>
              }
            />
            <div className="mt-8 grid gap-4">
              {[
                "Launch the local SaaS site and download the packaged desktop app.",
                "Open the app to start the local API, worker, and web runtime automatically.",
                "Paste a real local repository path into the empty intake workspace.",
                "Answer analysis questions, review reports, approve planning, and launch the local preview.",
              ].map((step, index) => (
                <div key={step} className="rounded-[1.5rem] border border-white/10 bg-white/[0.04] p-4">
                  <p className="text-xs uppercase tracking-[0.28em] text-slate-400">{`0${index + 1}`}</p>
                  <p className="mt-2 text-sm leading-6 text-slate-200">{step}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-4 rounded-[2rem] border border-white/10 bg-[linear-gradient(180deg,rgba(56,189,248,0.12),rgba(15,23,42,0.32))] p-6">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Judge-mode posture</p>
            <h2 className="text-3xl font-semibold text-white">No bundled dummy project is used in this path.</h2>
            <div className="space-y-3">
              {[
                "Workspace starts empty.",
                "Local-path scan stays read-only until planning is approved.",
                "Analysis questions and approvals are persisted in the control plane.",
                "Local preview launch is enabled only after planning approval.",
              ].map((item) => (
                <div key={item} className="rounded-[1.4rem] border border-white/10 bg-white/[0.05] px-4 py-3 text-sm leading-6 text-slate-200">
                  {item}
                </div>
              ))}
            </div>
            <Link href="/projects/new" className="inline-flex rounded-full border border-white/10 px-5 py-3 text-sm font-medium text-white transition hover:bg-white/[0.06]">
              Open intake workspace
            </Link>
          </div>
        </div>
      </main>
    );
  }

  let project = createMockProjectDataset("legacycart");
  let liveDataUnavailable = false;

  try {
    project = await loadProjectDataset("legacycart");
  } catch (error) {
    if (error instanceof BackendUnavailableError) {
      liveDataUnavailable = true;
    } else {
      throw error;
    }
  }

  return (
    <main className="mx-auto max-w-7xl px-6 pb-20 pt-14 lg:px-8">
      <div className="grid gap-10 lg:grid-cols-[1fr_0.95fr]">
        <div>
          <SectionHeader
            eyebrow="Interactive demo"
            title="Push the MTC dummy project into a GitHub repo and hand off into the cockpit."
            description="This page is intentionally task-first. It turns the bundled LegacyCart seed into a single demonstrable workflow instead of a presenter script."
            action={
              <Link href="/projects/legacycart" className="rounded-full border border-white/10 px-5 py-3 text-sm font-medium text-white">
                Skip to cockpit
              </Link>
            }
          />

          <div className="mt-8 rounded-[2rem] border border-white/10 bg-white/[0.04] p-6">
            <div className="flex flex-wrap items-center gap-3">
              <Badge tone="amber">{`${project.overview.readinessScore}% readiness`}</Badge>
              <Badge tone="rose">{`${project.findings.filter((item) => item.severity === "critical" || item.severity === "high").length} high-risk blockers`}</Badge>
              <Badge tone="green">{project.overview.recommendedProvider}</Badge>
            </div>
            <h2 className="mt-5 text-3xl font-semibold text-white">{project.projectName}</h2>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-300">{project.overview.narrative}</p>
            {liveDataUnavailable ? (
              <div className="mt-5 rounded-[1.4rem] border border-amber-400/30 bg-amber-400/10 px-4 py-3 text-sm leading-6 text-amber-100">
                The live control plane is unavailable right now, so this page is showing the bundled demo dataset until the local stack comes back up.
              </div>
            ) : null}
            <div className="mt-8 grid gap-4 md:grid-cols-2">
              {stages.map((stage) => (
                <div key={stage.title} className="rounded-[1.5rem] border border-white/10 bg-slate-950/35 p-4">
                  <h3 className="text-lg font-medium text-white">{stage.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-300">{stage.body}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-4 rounded-[2rem] border border-white/10 bg-[linear-gradient(180deg,rgba(56,189,248,0.12),rgba(15,23,42,0.32))] p-6">
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">What the workflow covers</p>
          <h2 className="text-3xl font-semibold text-white">One page replaces the old demo script.</h2>
          <div className="space-y-3">
            {checklist.map((item) => (
              <div key={item} className="rounded-[1.4rem] border border-white/10 bg-white/[0.05] px-4 py-3 text-sm leading-6 text-slate-200">
                {item}
              </div>
            ))}
          </div>
          <p className="text-sm leading-7 text-slate-300">
            The seeded project still opens into the same evidence-backed cockpit, with findings, reports, connectors,
            approvals, and scenario analysis already wired up.
          </p>
          <div className="rounded-[1.6rem] border border-white/10 bg-slate-950/40 p-4 text-sm leading-6 text-slate-300">
            Recommended handoff: run the workflow here, then open <span className="font-medium text-white">Connectors</span>,{" "}
            <span className="font-medium text-white">Overview</span>, and <span className="font-medium text-white">Findings</span>{" "}
            in the cockpit.
          </div>
        </div>
      </div>

      <div className="mt-10">
        <DemoWorkflowForm />
      </div>
    </main>
  );
}
