"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { Badge, Card } from "@/components/ui";
import { DEFAULT_WORKSPACE_ID, createWorkspaceProject } from "@/lib/app-api";

const starterHints = {
  simple: {
    label: "Simple rollout",
    note: "Lean hosting is probably enough for the first launch.",
  },
  balanced: {
    label: "Balanced rollout",
    note: "A simple AWS path or lightweight platform is the best starting point.",
  },
  scaled: {
    label: "Scale-up rollout",
    note: "Container or event-driven planning may be justified soon, but not by default.",
  },
} as const;

export function ProjectIntakeForm() {
  const router = useRouter();
  const [sourceTarget, setSourceTarget] = useState("");
  const [expectedUsers, setExpectedUsers] = useState(25);
  const [sourceKind, setSourceKind] = useState<"local_path" | "github">("local_path");
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const guidance =
    expectedUsers <= 50 ? starterHints.simple : expectedUsers <= 250 ? starterHints.balanced : starterHints.scaled;

  const inferredName =
    sourceTarget
      .split(/[\\/]/)
      .filter(Boolean)
      .at(-1)
      ?.replace(/\.[^/.]+$/, "")
      ?.replace(/[-_]+/g, " ")
      ?.replace(/\b\w/g, (letter) => letter.toUpperCase()) ?? "Local migration project";

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedTarget = sourceTarget.trim();
    if (!trimmedTarget) {
      setError("Paste a local path or repository URL to start the analysis.");
      return;
    }

    setError(null);
    startTransition(async () => {
      try {
        const project = await createWorkspaceProject(DEFAULT_WORKSPACE_ID, {
          name: inferredName,
          clientName: inferredName,
          sourceKind,
          sourceTarget: trimmedTarget,
          expectedUsers,
          preferredCloud: "aws",
          credentialLabel: sourceKind === "local_path" ? "Local path" : "GitHub token",
          credentialKind: sourceKind === "local_path" ? "none" : "token",
        });
        router.push(`/projects/${project.id}`);
        router.refresh();
      } catch (submissionError) {
        setError(submissionError instanceof Error ? submissionError.message : "The intake request failed.");
      }
    });
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
      <Card className="space-y-4">
        <div>
          <h2 className="text-lg font-medium text-white">Judge-ready project intake</h2>
          <p className="mt-2 text-sm leading-6 text-slate-300">
            Paste a real local path or GitHub URL and the swarm will start the first evidence-backed analysis from that source.
          </p>
        </div>
        <form className="space-y-4" onSubmit={handleSubmit}>
          <label className="block text-sm text-slate-200">
            Source type
            <select
              className="mt-2 w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white"
              value={sourceKind}
              onChange={(event) => setSourceKind(event.target.value as "local_path" | "github")}
            >
              <option value="local_path">Local path</option>
              <option value="github">GitHub URL</option>
            </select>
          </label>
          <label className="block text-sm text-slate-200">
            Local path or GitHub URL
            <input
              className="mt-2 w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white"
              value={sourceTarget}
              onChange={(event) => setSourceTarget(event.target.value)}
              placeholder={sourceKind === "local_path" ? "/Users/judge/projects/my-app" : "https://github.com/org/repo"}
            />
          </label>
          <label className="block text-sm text-slate-200">
            Expected users
            <input
              className="mt-2 w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white"
              type="number"
              min={1}
              value={expectedUsers}
              onChange={(event) => setExpectedUsers(Number(event.target.value))}
            />
          </label>
          {error ? <p className="text-sm text-rose-300">{error}</p> : null}
          <button
            type="submit"
            className="inline-flex rounded-full bg-sky-400 px-5 py-3 text-sm font-medium text-slate-950 transition hover:bg-sky-300 disabled:cursor-not-allowed disabled:opacity-70"
            disabled={isPending}
          >
            {isPending ? "Starting analysis..." : "Start analysis"}
          </button>
        </form>
      </Card>

      <Card className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-lg font-medium text-white">Recommended path for the current answers</h2>
          <Badge tone="blue">{guidance.label}</Badge>
        </div>
        <p className="text-sm leading-6 text-slate-300">{guidance.note}</p>
        <div className="space-y-3 text-sm leading-6 text-slate-300">
          <p>{sourceKind === "local_path" ? "The desktop app will scan the local repo directly and keep discovery read-only." : "The cockpit will connect the GitHub source once credentials are available."}</p>
          <p>
            For about {expectedUsers} users, the swarm should explain simple deployment options first and only recommend heavier cloud patterns if the codebase or risk profile demands them.
          </p>
          <p>Project label: {inferredName}</p>
          <p>Source: {sourceTarget || "Paste a path to begin."}</p>
        </div>
      </Card>
    </div>
  );
}
