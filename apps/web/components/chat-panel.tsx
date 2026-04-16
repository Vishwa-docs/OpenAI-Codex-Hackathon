"use client";

import type { ChatMessage } from "@contracts/index";
import { Badge, Card, SectionHeader } from "@/components/ui";
import { formatDateTime } from "@/lib/format";
import { useMemo, useState, type FormEvent } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export function ChatPanel({
  messages,
  projectName,
  projectId,
}: {
  messages: ChatMessage[];
  projectName: string;
  projectId: string;
}) {
  const [draft, setDraft] = useState("");
  const [thread, setThread] = useState(messages);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const lastAiMessage = useMemo(
    () => thread.filter((message) => message.role === "ai").at(-1),
    [thread]
  );

  async function refreshThread() {
    const response = await fetch(`${API_BASE}/projects/${projectId}/chat/messages`, {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`Unable to refresh thread (${response.status})`);
    }

    const payload = (await response.json()) as ChatMessage[];
    setThread(payload);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!draft.trim()) {
      return;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      const response = await fetch(`${API_BASE}/projects/${projectId}/chat/messages`, {
        method: "POST",
        headers: {
          "content-type": "application/json",
        },
        body: JSON.stringify({
          author: "You",
          role: "human",
          content: draft.trim(),
        }),
      });

      if (!response.ok) {
        throw new Error(`Unable to create message (${response.status})`);
      }

      setDraft("");
      await refreshThread();
    } catch {
      setError("The cockpit assistant could not be reached. Check that the API is running.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="space-y-5">
      <SectionHeader
        eyebrow="Stakeholder chat"
        title={`Ask questions about ${projectName}`}
        description="The assistant responds from the project dossier and keeps unsupported answers out of the path."
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
        <form className="space-y-3" onSubmit={handleSubmit}>
          <textarea
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            rows={4}
            className="w-full rounded-3xl border border-white/10 bg-ink-900/70 p-4 text-sm text-white outline-none transition placeholder:text-slate-500 focus:border-sky-400/50"
            placeholder="Ask about migration sequencing, provider choice, blockers, or planning approvals..."
          />
          {error ? <p className="text-sm text-rose-300">{error}</p> : null}
          <button
            type="submit"
            disabled={isSubmitting}
            className="rounded-full bg-sky-400 px-5 py-2.5 text-sm font-medium text-slate-950 transition hover:bg-sky-300"
          >
            {isSubmitting ? "Sending..." : "Send to cockpit assistant"}
          </button>
        </form>
      </Card>
    </div>
  );
}
