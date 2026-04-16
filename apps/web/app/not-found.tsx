import Link from "next/link";

export default function NotFound() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-ink-950 px-6 text-slate-100">
      <div className="max-w-xl space-y-5 text-center">
        <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Not found</p>
        <h1 className="text-4xl font-semibold text-white">This route is outside the current cockpit map.</h1>
        <p className="text-sm leading-7 text-slate-300">Try the dashboard or open the projects workspace to continue.</p>
        <div className="flex justify-center gap-3">
          <Link href="/dashboard" className="rounded-full bg-sky-400 px-5 py-3 text-sm font-medium text-slate-950">
            Open dashboard
          </Link>
          <Link href="/projects" className="rounded-full border border-white/15 px-5 py-3 text-sm text-white">
            Open projects
          </Link>
        </div>
      </div>
    </main>
  );
}
