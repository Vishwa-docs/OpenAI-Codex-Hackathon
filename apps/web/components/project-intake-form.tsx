"use client";

import { useState } from "react";
import { Badge, Card } from "@/components/ui";

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
  const [sourceTarget, setSourceTarget] = useState("demo-systems/legacycart");
  const [expectedUsers, setExpectedUsers] = useState(25);
  const [sourceKind, setSourceKind] = useState<"local_directory" | "github">("local_directory");

  const guidance =
    expectedUsers <= 50 ? starterHints.simple : expectedUsers <= 250 ? starterHints.balanced : starterHints.scaled;

  return (
    <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
      <Card className="space-y-4">
        <div>
          <h2 className="text-lg font-medium text-white">Guided project intake</h2>
          <p className="mt-2 text-sm leading-6 text-slate-300">
            Start with the code location and expected users so the swarm can keep its first recommendation realistic.
          </p>
        </div>
        <label className="block text-sm text-slate-200">
          Source type
          <select
            className="mt-2 w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white"
            value={sourceKind}
            onChange={(event) => setSourceKind(event.target.value as "local_directory" | "github")}
          >
            <option value="local_directory">Local directory</option>
            <option value="github">GitHub URL</option>
          </select>
        </label>
        <label className="block text-sm text-slate-200">
          Local path or GitHub URL
          <input
            className="mt-2 w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white"
            value={sourceTarget}
            onChange={(event) => setSourceTarget(event.target.value)}
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
      </Card>

      <Card className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-lg font-medium text-white">Recommended path for the current answers</h2>
          <Badge tone="blue">{guidance.label}</Badge>
        </div>
        <p className="text-sm leading-6 text-slate-300">{guidance.note}</p>
        <div className="space-y-3 text-sm leading-6 text-slate-300">
          <p>{sourceKind === "local_directory" ? "The desktop app can scan the local repo directly." : "The cockpit will connect the GitHub source once credentials are available."}</p>
          <p>
            For about {expectedUsers} users, the swarm should explain simple deployment options first and only recommend heavier cloud patterns if the codebase or risk profile demands them.
          </p>
          <p>Source: {sourceTarget}</p>
        </div>
      </Card>
    </div>
  );
}
