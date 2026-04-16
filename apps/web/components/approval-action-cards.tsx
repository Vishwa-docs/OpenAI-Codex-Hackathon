"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import type { ApprovalRecord } from "@contracts/index";
import { Badge, Card } from "@/components/ui";
import { decideApproval } from "@/lib/app-api";

export function ApprovalActionCards({
  projectId,
  approvals,
}: {
  projectId: string;
  approvals: ApprovalRecord[];
}) {
  const router = useRouter();
  const [comments, setComments] = useState<Record<string, string>>(
    Object.fromEntries(approvals.map((approval) => [approval.id, approval.comment ?? ""]))
  );
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function submitDecision(approval: ApprovalRecord, decision: "approved" | "rejected") {
    const comment = comments[approval.id]?.trim() || (decision === "approved" ? "Approved in the judge workspace." : "Rejected in the judge workspace.");
    setError(null);
    startTransition(async () => {
      try {
        await decideApproval(projectId, approval.id, {
          decision,
          actor: "Judge Operator",
          comment,
        });
        router.refresh();
      } catch (submissionError) {
        setError(submissionError instanceof Error ? submissionError.message : "Unable to record the approval decision.");
      }
    });
  }

  return (
    <div className="space-y-4">
      {approvals.map((approval) => (
        <Card key={approval.id} className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.28em] text-slate-400">{approval.phase}</p>
              <h3 className="mt-2 text-lg font-medium text-white">Approval {approval.id}</h3>
            </div>
            <Badge tone={approval.state === "approved" ? "green" : approval.state === "pending" ? "amber" : "slate"}>
              {approval.state}
            </Badge>
          </div>
          <textarea
            className="min-h-24 w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-white"
            value={comments[approval.id] ?? ""}
            onChange={(event) => setComments((current) => ({ ...current, [approval.id]: event.target.value }))}
            placeholder="Record why this phase is being approved or rejected."
          />
          <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-slate-300">
            <div className="flex flex-wrap gap-4">
              <span>Requested by {approval.requestedBy}</span>
              {approval.approver ? <span>Approved by {approval.approver}</span> : null}
              {approval.decidedAt ? <span>Decision recorded</span> : null}
            </div>
            {approval.state === "pending" ? (
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => submitDecision(approval, "rejected")}
                  disabled={isPending}
                  className="rounded-full border border-white/10 px-4 py-2 text-sm font-medium text-white transition hover:bg-white/[0.06] disabled:cursor-not-allowed disabled:opacity-70"
                >
                  Reject
                </button>
                <button
                  type="button"
                  onClick={() => submitDecision(approval, "approved")}
                  disabled={isPending}
                  className="rounded-full bg-sky-400 px-4 py-2 text-sm font-medium text-slate-950 transition hover:bg-sky-300 disabled:cursor-not-allowed disabled:opacity-70"
                >
                  Approve
                </button>
              </div>
            ) : null}
          </div>
        </Card>
      ))}
      {error ? <p className="text-sm text-rose-300">{error}</p> : null}
    </div>
  );
}
