"use client";

import { Badge, Card, SectionHeader } from "@/components/ui";
import { formatDateTime } from "@/lib/format";
import type { ChatMessage } from "@/lib/mock-data";
import { useMemo, useState } from "react";

function seededReply(input: string) {
  const normalized = input.toLowerCase();
  if (normalized.includes("database first")) {
    return "Database-first is viable only after the hardcoded secret and log redaction issues are remediated. The cockpit keeps the recommendation at re-architect-first for now.";
  }
  if (normalized.includes("provider")) {
    return "AWS remains the lead provider in the seeded assessment because the workload needs a strong landing zone, IAM, and managed database path.";
  }
  return "I can answer from the seeded dossier and evidence set. The key blocker is the security posture, followed by the brittle ops model and external integration constraints.";
}

export function ChatPanel({
  messages,
  projectName
}: {
  messages: ChatMessage[];
  projectName: string;
}) {
  const [draft, setDraft] = useState("");
  const [thread, setThread] = useState(messages);

  const lastAiMessage = useMemo(
    () => thread.filter((message) => message.role === "ai").at(-1),
    [thread]
  );

  return (
    <div className="space-y-5">
      <SectionHeader
        eyebrow="Stakeholder chat"
        title={`Ask questions about ${projectName}`}
        description="The assistant responds from the seeded evidence bundle and keeps unsafe or unsupported answers out of the path."
      />
      <Card className="space-y-4">
        {thread.map((message) => (
          <div
            key={message.id}
            className={`max-w-3xl rounded-3xl px-4 py-3 ${message.role === "human" ? "ml-auto bg-sky-400/15 text-slate-50" : "bg-white/[0.06] text-slate-100"}`}
          >
            <div className="flex items-center justify-between gap-4 text-xs uppercase tracking-[0.22em] text-slate-400">
              <span>{message.author}</span>
              <span>{formatDateTime(message.createdAt)}</span>
            </div>
            <p className="mt-2 text-sm leading-6">{message.content}</p>
          </div>
        ))}
      </Card>
      <Card className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <Badge tone="blue">Evidence-backed</Badge>
          <span className="text-sm text-slate-300">Latest answer: {lastAiMessage?.author ?? "none yet"}</span>
        </div>
        <form
          className="space-y-3"
          onSubmit={(event) => {
            event.preventDefault();
            if (!draft.trim()) return;
            const humanMessage: ChatMessage = {
              id: `chat-${thread.length + 1}`,
              author: "You",
              role: "human",
              createdAt: new Date().toISOString(),
              content: draft.trim()
            };
            const aiMessage: ChatMessage = {
              id: `chat-${thread.length + 2}`,
              author: "Cockpit Assistant",
              role: "ai",
              createdAt: new Date().toISOString(),
              content: seededReply(draft)
            };
            setThread((current) => [...current, humanMessage, aiMessage]);
            setDraft("");
          }}
        >
          <textarea
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            rows={4}
            className="w-full rounded-3xl border border-white/10 bg-ink-900/70 p-4 text-sm text-white outline-none transition placeholder:text-slate-500 focus:border-sky-400/50"
            placeholder="Ask about migration sequencing, provider choice, blockers, or planning approvals..."
          />
          <button
            type="submit"
            className="rounded-full bg-sky-400 px-5 py-2.5 text-sm font-medium text-slate-950 transition hover:bg-sky-300"
          >
            Send to cockpit assistant
          </button>
        </form>
      </Card>
    </div>
  );
}
