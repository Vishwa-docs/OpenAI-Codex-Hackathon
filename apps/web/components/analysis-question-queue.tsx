"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import type { AnalysisQuestion } from "@contracts/index";
import { Badge } from "@/components/ui";
import { answerAnalysisQuestion } from "@/lib/app-api";

export function AnalysisQuestionQueue({
  projectId,
  questions,
}: {
  projectId: string;
  questions: AnalysisQuestion[];
}) {
  const router = useRouter();
  const [answers, setAnswers] = useState<Record<string, string>>(
    Object.fromEntries(questions.map((question) => [question.id, question.answer ?? ""]))
  );
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  if (questions.length === 0) {
    return (
      <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="text-base font-medium text-white">No unanswered analysis questions</h3>
            <p className="mt-3 text-sm leading-6 text-slate-300">
              The swarm has enough context to move into report review and planning approval.
            </p>
          </div>
          <Badge tone="green">ready</Badge>
        </div>
      </div>
    );
  }

  function handleSubmit(question: AnalysisQuestion) {
    const answer = answers[question.id]?.trim();
    if (!answer) {
      setError("Enter an answer before saving it back to the swarm.");
      return;
    }

    setError(null);
    startTransition(async () => {
      try {
        await answerAnalysisQuestion(projectId, question.id, {
          actor: "Judge Operator",
          answer,
        });
        router.refresh();
      } catch (submissionError) {
        setError(submissionError instanceof Error ? submissionError.message : "Unable to save the answer.");
      }
    });
  }

  return (
    <div className="space-y-3">
      {questions.map((question) => {
        const answer = answers[question.id] ?? "";
        const isAnswered = question.state === "answered";
        return (
          <div key={question.id} className="rounded-3xl border border-white/10 bg-white/[0.04] p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-base font-medium text-white">{question.question}</h3>
                <p className="mt-1 text-xs uppercase tracking-[0.22em] text-sky-200/80">{question.stage.replace(/_/g, " ")}</p>
              </div>
              <Badge tone={isAnswered ? "green" : "amber"}>{isAnswered ? "answer recorded" : "answer required"}</Badge>
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-300">{question.rationale}</p>
            <textarea
              className="mt-4 min-h-28 w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-white"
              value={answer}
              onChange={(event) => setAnswers((current) => ({ ...current, [question.id]: event.target.value }))}
              placeholder="Answer with the business, compliance, or rollout detail the swarm needs."
            />
            <div className="mt-4 flex items-center justify-between gap-3">
              <p className="text-sm text-slate-400">{isAnswered ? "Update the answer if the plan changes." : "This answer feeds the next planning pass."}</p>
              <button
                type="button"
                onClick={() => handleSubmit(question)}
                disabled={isPending}
                className="rounded-full bg-sky-400 px-4 py-2 text-sm font-medium text-slate-950 transition hover:bg-sky-300 disabled:cursor-not-allowed disabled:opacity-70"
              >
                {isPending ? "Saving..." : isAnswered ? "Update answer" : "Save answer"}
              </button>
            </div>
          </div>
        );
      })}
      {error ? <p className="text-sm text-rose-300">{error}</p> : null}
    </div>
  );
}
