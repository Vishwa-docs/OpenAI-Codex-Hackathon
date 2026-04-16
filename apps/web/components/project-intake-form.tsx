"use client";

import type { ProjectCreate } from "@contracts/index";
import { useRouter } from "next/navigation";
import { useState, type ChangeEvent, type FormEvent } from "react";

import { createWorkspaceProject } from "@/lib/app-api";
import { Card } from "@/components/ui";

const defaultDraft: ProjectCreate = {
  name: "",
  clientName: "",
  sourceSystem: "",
  targetSystem: "",
  businessSummary: "",
  owner: "",
  primaryRegion: "us-east-1",
  complianceTags: [],
};

export function ProjectIntakeForm({ workspaceId }: { workspaceId: string }) {
  const router = useRouter();
  const [draft, setDraft] = useState<ProjectCreate>(defaultDraft);
  const [complianceInput, setComplianceInput] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function updateField<Key extends keyof ProjectCreate>(key: Key, value: ProjectCreate[Key]) {
    setDraft((current) => ({ ...current, [key]: value }));
  }

  function handleInput(key: keyof ProjectCreate) {
    return (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      updateField(key, event.target.value as ProjectCreate[typeof key]);
    };
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const payload: ProjectCreate = {
        ...draft,
        complianceTags: complianceInput
          .split(",")
          .map((value) => value.trim())
          .filter(Boolean),
      };
      const project = await createWorkspaceProject(workspaceId, payload);
      router.push(`/projects/${project.id}`);
      router.refresh();
    } catch {
      setError("The project could not be created. Verify that the API is running and try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Card className="space-y-4">
      <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSubmit}>
        <label className="space-y-2 text-sm text-slate-300">
          <span className="font-medium text-white">Project name</span>
          <input
            value={draft.name}
            onChange={handleInput("name")}
            required
            className="w-full rounded-2xl border border-white/10 bg-ink-900/70 px-4 py-3 text-white outline-none transition focus:border-sky-400/50"
            placeholder="Northstar checkout modernization"
          />
        </label>
        <label className="space-y-2 text-sm text-slate-300">
          <span className="font-medium text-white">Client</span>
          <input
            value={draft.clientName}
            onChange={handleInput("clientName")}
            required
            className="w-full rounded-2xl border border-white/10 bg-ink-900/70 px-4 py-3 text-white outline-none transition focus:border-sky-400/50"
            placeholder="Northstar Retail"
          />
        </label>
        <label className="space-y-2 text-sm text-slate-300 md:col-span-2">
          <span className="font-medium text-white">Source system</span>
          <textarea
            value={draft.sourceSystem}
            onChange={handleInput("sourceSystem")}
            required
            rows={3}
            className="w-full rounded-2xl border border-white/10 bg-ink-900/70 px-4 py-3 text-white outline-none transition focus:border-sky-400/50"
            placeholder="On-prem Java monolith with PostgreSQL, cron jobs, and shared NFS storage"
          />
        </label>
        <label className="space-y-2 text-sm text-slate-300 md:col-span-2">
          <span className="font-medium text-white">Target system</span>
          <textarea
            value={draft.targetSystem}
            onChange={handleInput("targetSystem")}
            required
            rows={3}
            className="w-full rounded-2xl border border-white/10 bg-ink-900/70 px-4 py-3 text-white outline-none transition focus:border-sky-400/50"
            placeholder="AWS landing zone with managed Postgres, object storage, and approval-gated CI/CD"
          />
        </label>
        <label className="space-y-2 text-sm text-slate-300 md:col-span-2">
          <span className="font-medium text-white">Business summary</span>
          <textarea
            value={draft.businessSummary}
            onChange={handleInput("businessSummary")}
            required
            rows={4}
            className="w-full rounded-2xl border border-white/10 bg-ink-900/70 px-4 py-3 text-white outline-none transition focus:border-sky-400/50"
            placeholder="Revenue-critical commerce flow with seasonal spikes, customer PII, and executive pressure to modernize safely."
          />
        </label>
        <label className="space-y-2 text-sm text-slate-300">
          <span className="font-medium text-white">Project owner</span>
          <input
            value={draft.owner}
            onChange={handleInput("owner")}
            required
            className="w-full rounded-2xl border border-white/10 bg-ink-900/70 px-4 py-3 text-white outline-none transition focus:border-sky-400/50"
            placeholder="Taylor Reed"
          />
        </label>
        <label className="space-y-2 text-sm text-slate-300">
          <span className="font-medium text-white">Primary region</span>
          <input
            value={draft.primaryRegion}
            onChange={handleInput("primaryRegion")}
            required
            className="w-full rounded-2xl border border-white/10 bg-ink-900/70 px-4 py-3 text-white outline-none transition focus:border-sky-400/50"
            placeholder="us-east-1"
          />
        </label>
        <label className="space-y-2 text-sm text-slate-300 md:col-span-2">
          <span className="font-medium text-white">Compliance tags</span>
          <input
            value={complianceInput}
            onChange={(event) => setComplianceInput(event.target.value)}
            className="w-full rounded-2xl border border-white/10 bg-ink-900/70 px-4 py-3 text-white outline-none transition focus:border-sky-400/50"
            placeholder="PCI DSS, SOC 2, HIPAA"
          />
        </label>
        {error ? <p className="md:col-span-2 text-sm text-rose-300">{error}</p> : null}
        <div className="md:col-span-2 flex items-center justify-between gap-4">
          <p className="max-w-2xl text-sm leading-6 text-slate-300">
            Projects are created in intake mode with read-only defaults. Source and cloud connectors can be added after the workspace record exists.
          </p>
          <button
            type="submit"
            disabled={isSubmitting}
            className="rounded-full bg-sky-400 px-5 py-2.5 text-sm font-medium text-slate-950 transition hover:bg-sky-300 disabled:cursor-not-allowed disabled:bg-slate-500"
          >
            {isSubmitting ? "Creating..." : "Create project"}
          </button>
        </div>
      </form>
    </Card>
  );
}
