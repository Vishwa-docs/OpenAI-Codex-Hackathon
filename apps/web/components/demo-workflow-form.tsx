"use client";

import Link from "next/link";
import { useState, useTransition } from "react";

type WorkflowStep = {
  key: string;
  title: string;
  status: "pending" | "skipped" | "succeeded" | "failed";
  detail: string;
};

type WorkflowResult = {
  workflowId: string;
  projectId: string;
  sourceProjectId: string;
  targetRepoUrl: string;
  targetBranch: string;
  status: "completed" | "simulated";
  summary: string;
  steps: WorkflowStep[];
  cockpitPath: string;
  warnings: string[];
};

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

const initialSteps: WorkflowStep[] = [
  {
    key: "validate_target",
    title: "Validate target repository",
    status: "pending",
    detail: "We confirm the GitHub URL and branch shape before touching the seed project."
  },
  {
    key: "prepare_seed",
    title: "Prepare LegacyCart seed",
    status: "pending",
    detail: "The demo copies the seeded legacy system into a temporary git workspace."
  },
  {
    key: "push_seed",
    title: "Push seed branch",
    status: "pending",
    detail: "If a GitHub token is supplied, the workflow creates and pushes the target branch."
  },
  {
    key: "register_source",
    title: "Register source connection",
    status: "pending",
    detail: "The cockpit records the target repository as the active source connection."
  },
  {
    key: "queue_assessment",
    title: "Queue assessment run",
    status: "pending",
    detail: "A local-worker assessment run is created so the cockpit can open on a real workflow state."
  }
];

export function DemoWorkflowForm() {
  const [targetRepoUrl, setTargetRepoUrl] = useState("");
  const [branch, setBranch] = useState("mtc-demo");
  const [actor, setActor] = useState("Demo operator");
  const [accessToken, setAccessToken] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<WorkflowResult | null>(null);
  const [isPending, startTransition] = useTransition();

  const handleSubmit = (formData: FormData) => {
    const repoUrl = String(formData.get("targetRepoUrl") ?? "").trim();
    const branchName = String(formData.get("branch") ?? "").trim();
    const actorName = String(formData.get("actor") ?? "").trim();
    const token = String(formData.get("accessToken") ?? "").trim();

    setError(null);
    setResult(null);

    startTransition(async () => {
      try {
        const response = await fetch(`${apiBase}/demo/github-seed`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            targetRepoUrl: repoUrl,
            branch: branchName,
            actor: actorName,
            accessToken: token || undefined,
            simulateOnly: token.length === 0
          })
        });

        const payload = (await response.json()) as WorkflowResult | { detail?: string };

        if (!response.ok) {
          throw new Error("detail" in payload && payload.detail ? payload.detail : "The workflow could not be started.");
        }

        setResult(payload as WorkflowResult);
      } catch (submissionError) {
        const message = submissionError instanceof Error ? submissionError.message : "The workflow could not be started.";
        setError(message);
      }
    });
  };

  const renderedSteps = result?.steps ?? initialSteps;
  const livePushEnabled = accessToken.trim().length > 0;

  return (
    <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
      <form
        action={handleSubmit}
        className="rounded-[2rem] border border-white/10 bg-white/[0.04] p-6 shadow-glow backdrop-blur"
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-sky-200/80">Run workflow</p>
            <h2 className="mt-3 text-3xl font-semibold text-white">Paste a GitHub repo and seed it with LegacyCart.</h2>
          </div>
          <span className="rounded-full border border-white/10 px-3 py-1 text-xs uppercase tracking-[0.24em] text-slate-300">
            {livePushEnabled ? "Live push" : "Simulation"}
          </span>
        </div>

        <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-300">
          The demo copies the bundled MTC dummy project into a temporary repository, pushes a branch to your target
          repo when a token is available, then creates a fresh assessment run for the cockpit.
        </p>

        <div className="mt-8 grid gap-5">
          <label className="grid gap-2">
            <span className="text-sm font-medium text-white">Target GitHub repository URL</span>
            <input
              name="targetRepoUrl"
              type="url"
              required
              placeholder="https://github.com/your-org/mtc-demo-target"
              value={targetRepoUrl}
              onChange={(event) => setTargetRepoUrl(event.target.value)}
              className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-white outline-none transition focus:border-sky-300/60"
            />
          </label>

          <div className="grid gap-5 md:grid-cols-2">
            <label className="grid gap-2">
              <span className="text-sm font-medium text-white">Branch</span>
              <input
                name="branch"
                type="text"
                required
                value={branch}
                onChange={(event) => setBranch(event.target.value)}
                className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-white outline-none transition focus:border-sky-300/60"
              />
            </label>
            <label className="grid gap-2">
              <span className="text-sm font-medium text-white">Triggered by</span>
              <input
                name="actor"
                type="text"
                required
                value={actor}
                onChange={(event) => setActor(event.target.value)}
                className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-white outline-none transition focus:border-sky-300/60"
              />
            </label>
          </div>

          <label className="grid gap-2">
            <span className="text-sm font-medium text-white">GitHub personal access token</span>
            <input
              name="accessToken"
              type="password"
              value={accessToken}
              onChange={(event) => setAccessToken(event.target.value)}
              placeholder="Optional for live push. Leave blank to run a safe simulation."
              className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-white outline-none transition focus:border-sky-300/60"
            />
            <span className="text-xs leading-6 text-slate-400">
              Blank token means we simulate the push and still register the source plus queue the assessment. Add a
              token to perform the live branch push.
            </span>
          </label>
        </div>

        {error ? (
          <div className="mt-6 rounded-2xl border border-rose-400/20 bg-rose-400/[0.08] px-4 py-3 text-sm leading-6 text-rose-100">
            {error}
          </div>
        ) : null}

        <div className="mt-8 flex flex-wrap items-center gap-3">
          <button
            type="submit"
            disabled={isPending}
            className="rounded-full bg-sky-400 px-6 py-3 text-sm font-medium text-slate-950 transition hover:bg-sky-300 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {isPending ? "Running workflow..." : livePushEnabled ? "Run live workflow" : "Run safe simulation"}
          </button>
          <Link
            href="/projects/legacycart"
            className="rounded-full border border-white/10 px-6 py-3 text-sm font-medium text-white transition hover:bg-white/[0.06]"
          >
            View seeded cockpit
          </Link>
        </div>
      </form>

      <div className="rounded-[2rem] border border-white/10 bg-slate-950/40 p-6">
        <div className="flex items-end justify-between gap-4 border-b border-white/10 pb-4">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Workflow timeline</p>
            <h2 className="mt-3 text-2xl font-semibold text-white">One page, one branch push, one cockpit handoff.</h2>
          </div>
          {result ? (
            <span className="rounded-full bg-emerald-400/12 px-3 py-1 text-xs uppercase tracking-[0.24em] text-emerald-100">
              {result.status}
            </span>
          ) : null}
        </div>

        <div className="mt-6 space-y-4">
          {renderedSteps.map((step, index) => {
            const tone =
              step.status === "succeeded"
                ? "border-emerald-400/25 bg-emerald-400/[0.07] text-emerald-100"
                : step.status === "failed"
                  ? "border-rose-400/25 bg-rose-400/[0.07] text-rose-100"
                  : step.status === "skipped"
                    ? "border-amber-400/25 bg-amber-400/[0.07] text-amber-100"
                    : "border-white/10 bg-white/[0.03] text-slate-200";

            return (
              <div key={step.key} className={`rounded-[1.6rem] border px-4 py-4 ${tone}`}>
                <div className="flex items-start gap-4">
                  <span className="mt-0.5 text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">{`0${index + 1}`}</span>
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-3">
                      <h3 className="text-sm font-medium text-white">{step.title}</h3>
                      <span className="rounded-full border border-current/20 px-2 py-0.5 text-[11px] uppercase tracking-[0.18em]">
                        {step.status}
                      </span>
                    </div>
                    <p className="mt-2 text-sm leading-6 text-slate-300">{step.detail}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {result ? (
          <div className="mt-6 rounded-[1.6rem] border border-white/10 bg-white/[0.04] p-4">
            <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Result</p>
            <p className="mt-3 text-lg font-medium text-white">{result.summary}</p>
            <p className="mt-2 text-sm leading-6 text-slate-300">
              Workflow <span className="font-medium text-white">{result.workflowId}</span> targeted{" "}
              <span className="font-medium text-white">{result.targetBranch}</span> on{" "}
              <span className="font-medium text-white">{result.targetRepoUrl}</span>.
            </p>
            {result.warnings.length > 0 ? (
              <div className="mt-4 rounded-2xl border border-amber-400/20 bg-amber-400/[0.08] px-4 py-3 text-sm leading-6 text-amber-100">
                {result.warnings.join(" ")}
              </div>
            ) : null}
            <div className="mt-5 flex flex-wrap gap-3">
              <Link
                href={result.cockpitPath}
                className="rounded-full bg-white px-5 py-2 text-sm font-medium text-slate-950 transition hover:bg-slate-200"
              >
                Open cockpit handoff
              </Link>
              <Link
                href="/projects/legacycart/connectors"
                className="rounded-full border border-white/10 px-5 py-2 text-sm font-medium text-white transition hover:bg-white/[0.06]"
              >
                Inspect connector state
              </Link>
            </div>
          </div>
        ) : (
          <div className="mt-6 rounded-[1.6rem] border border-dashed border-white/15 px-4 py-4 text-sm leading-6 text-slate-300">
            The right panel turns into a live execution trace once the workflow starts.
          </div>
        )}
      </div>
    </div>
  );
}
