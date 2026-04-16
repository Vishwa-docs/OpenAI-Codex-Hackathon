"use client";

import { isBackendUnavailableError } from "@/lib/app-errors";
import Link from "next/link";

export function AppErrorState({
  error,
  reset,
  title = "The cockpit cannot reach the backend right now."
}: {
  error: Error & { digest?: string };
  reset: () => void;
  title?: string;
}) {
  const details = isBackendUnavailableError(error)
    ? `The app tried to load ${error.sourcePath}, but the API did not respond.`
    : "An unexpected error reached the authenticated app surface.";

  return (
    <main className="min-h-screen bg-ink-950 px-6 py-16 text-slate-100">
      <div className="mx-auto flex max-w-2xl flex-col gap-6 rounded-[28px] border border-white/10 bg-white/5 p-8 shadow-glow backdrop-blur">
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">App error</p>
          <h1 className="text-3xl font-semibold text-white">{title}</h1>
          <p className="text-sm leading-6 text-slate-300">{details}</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={reset}
            className="rounded-full bg-sky-400 px-5 py-2.5 text-sm font-medium text-slate-950 transition hover:bg-sky-300"
          >
            Try again
          </button>
          <Link
            href="/sign-in"
            className="rounded-full border border-white/15 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-white/[0.08]"
          >
            Return to sign in
          </Link>
        </div>
      </div>
    </main>
  );
}
