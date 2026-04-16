import { marketingNav } from "@/lib/navigation";
import Link from "next/link";
import type { ReactNode } from "react";

export function MarketingShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-ink-950 text-slate-100">
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top_left,rgba(56,189,248,0.16),transparent_35%),radial-gradient(circle_at_bottom_right,rgba(59,130,246,0.14),transparent_40%)]" />
      <header className="sticky top-0 z-40 border-b border-white/10 bg-ink-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4 lg:px-8">
          <Link href="/" className="text-sm font-semibold tracking-[0.25em] text-white">
            CLOUD MIGRATION COCKPIT
          </Link>
          <nav className="hidden items-center gap-1 md:flex">
            {marketingNav.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="rounded-full px-4 py-2 text-sm text-slate-300 transition hover:bg-white/[0.06] hover:text-white"
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <div className="flex items-center gap-3">
            <Link href="/projects/legacycart" className="hidden text-sm text-slate-300 transition hover:text-white lg:inline-flex">
              Preview cockpit
            </Link>
            <Link
              href="/demo"
              className="rounded-full bg-sky-400 px-4 py-2 text-sm font-medium text-slate-950 transition hover:bg-sky-300"
            >
              Run demo
            </Link>
          </div>
        </div>
      </header>
      {children}
    </div>
  );
}
