"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import type { PreviewDeploymentStatus } from "@contracts/index";
import { Badge, Card } from "@/components/ui";
import { launchLocalPreview } from "@/lib/app-api";

export function PreviewLaunchCard({
  projectId,
  previewStatus,
  planningApproved,
}: {
  projectId: string;
  previewStatus: PreviewDeploymentStatus;
  planningApproved: boolean;
}) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function handleLaunch() {
    setError(null);
    startTransition(async () => {
      try {
        await launchLocalPreview(projectId, { triggeredBy: "Judge Operator" });
        router.refresh();
      } catch (launchError) {
        setError(launchError instanceof Error ? launchError.message : "Unable to launch the preview.");
      }
    });
  }

  return (
    <Card className="space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Local preview</p>
          <h3 className="mt-2 text-xl font-medium text-white">Launch the working copy into a local browser preview</h3>
        </div>
        <Badge tone={previewStatus.supported ? "blue" : "amber"}>{previewStatus.status}</Badge>
      </div>
      <p className="text-sm leading-6 text-slate-300">{previewStatus.summary}</p>
      {previewStatus.healthSummary ? <p className="text-sm leading-6 text-sky-100/80">{previewStatus.healthSummary}</p> : null}
      {previewStatus.url ? (
        <a
          href={previewStatus.url}
          target="_blank"
          rel="noreferrer"
          className="inline-flex text-sm font-medium text-sky-200 transition hover:text-sky-100"
        >
          Open preview: {previewStatus.url}
        </a>
      ) : null}
      {previewStatus.workspacePath ? <p className="text-sm text-slate-400">Working copy: {previewStatus.workspacePath}</p> : null}
      {previewStatus.logTail.length > 0 ? (
        <div className="rounded-2xl border border-white/10 bg-slate-950/70 p-4">
          <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Recent logs</p>
          <pre className="mt-3 whitespace-pre-wrap text-xs leading-6 text-slate-200">{previewStatus.logTail.join("\n")}</pre>
        </div>
      ) : null}
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-slate-400">
          {planningApproved
            ? "Planning approval is in place, so the preview can launch from the copied workspace."
            : "Approve the planning phase first. The preview launcher stays gated until the workflow is finalized."}
        </p>
        <button
          type="button"
          onClick={handleLaunch}
          disabled={isPending || !planningApproved || !previewStatus.supported}
          className="rounded-full bg-sky-400 px-4 py-2 text-sm font-medium text-slate-950 transition hover:bg-sky-300 disabled:cursor-not-allowed disabled:opacity-70"
        >
          {isPending ? "Launching..." : "Launch local preview"}
        </button>
      </div>
      {error ? <p className="text-sm text-rose-300">{error}</p> : null}
    </Card>
  );
}
