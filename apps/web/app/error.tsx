"use client";

import Link from "next/link";

export default function GlobalError({
  error,
  reset
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body className="flex min-h-screen items-center justify-center bg-ink-950 px-6 text-slate-100">
        <div className="max-w-xl space-y-5 text-center">
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Unexpected error</p>
          <h1 className="text-4xl font-semibold text-white">The cockpit hit an unexpected condition.</h1>
          <p className="text-sm leading-7 text-slate-300">{error.message}</p>
          <div className="flex justify-center gap-3">
            <button
              type="button"
              onClick={reset}
              className="rounded-full bg-sky-400 px-5 py-3 text-sm font-medium text-slate-950"
            >
              Retry
            </button>
            <Link href="/dashboard" className="rounded-full border border-white/15 px-5 py-3 text-sm text-white">
              Dashboard
            </Link>
          </div>
        </div>
      </body>
    </html>
  );
}
