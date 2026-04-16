"use client";

import { cockpitNav } from "@/lib/navigation";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

export function CockpitShell({
  children,
  projectHref = "/projects/legacycart"
}: {
  children: ReactNode;
  projectHref?: string;
}) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-ink-950 text-slate-100">
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top,rgba(14,165,233,0.14),transparent_35%),linear-gradient(to_bottom,rgba(255,255,255,0.03),transparent_20%)]" />
      <div className="mx-auto grid min-h-screen max-w-[1600px] gap-6 px-4 py-4 lg:grid-cols-[280px_minmax(0,1fr)] lg:px-6">
        <aside className="rounded-[28px] border border-white/10 bg-white/5 p-5 shadow-glow backdrop-blur">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Cockpit</p>
              <h1 className="mt-2 text-xl font-semibold text-white">Cloud Migration Cockpit</h1>
            </div>
          </div>
          <div className="mt-6 rounded-3xl border border-sky-400/20 bg-sky-400/10 p-4">
            <p className="text-xs uppercase tracking-[0.25em] text-sky-100/70">Current project</p>
            <p className="mt-2 text-lg font-medium text-white">LegacyCart</p>
            <p className="mt-1 text-sm text-slate-300">Northwind Retail Group</p>
            <Link
              href={projectHref}
              className="mt-4 inline-flex rounded-full bg-sky-400 px-3 py-2 text-sm font-medium text-slate-950 transition hover:bg-sky-300"
            >
              Open overview
            </Link>
          </div>
          <nav className="mt-6 space-y-1">
            {cockpitNav.map((item) => {
              const active = pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center justify-between rounded-2xl px-4 py-3 text-sm transition",
                    active ? "bg-white/10 text-white" : "text-slate-300 hover:bg-white/[0.06] hover:text-white"
                  )}
                >
                  <span>{item.label}</span>
                  {active ? <span className="h-2 w-2 rounded-full bg-sky-400" /> : null}
                </Link>
              );
            })}
          </nav>
        </aside>
        <main className="min-w-0 rounded-[28px] border border-white/10 bg-white/5 p-4 shadow-glow backdrop-blur lg:p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
