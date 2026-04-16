"use client";

import { projectNav } from "@/lib/navigation";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { usePathname } from "next/navigation";

export function ProjectShell({
  projectId,
  projectName,
  clientName
}: {
  projectId: string;
  projectName: string;
  clientName: string;
}) {
  const pathname = usePathname();
  const base = `/projects/${projectId}`;

  return (
    <div className="mb-6 rounded-[28px] border border-white/10 bg-white/[0.06] p-4">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-slate-400">{clientName}</p>
          <h2 className="mt-2 text-2xl font-semibold text-white">{projectName}</h2>
        </div>
        <div className="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-4 py-2 text-sm text-emerald-100">
          Workspace ready
        </div>
      </div>
      <div className="mt-5 flex flex-wrap gap-2">
        {projectNav.map((item) => {
          const href = item.href ? `${base}${item.href}` : base;
          const active = item.href ? pathname === href : pathname === base;
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "rounded-full px-4 py-2 text-sm transition",
                active ? "bg-sky-400 text-slate-950" : "bg-white/[0.06] text-slate-300 hover:bg-white/10 hover:text-white"
              )}
            >
              {item.label}
            </Link>
          );
        })}
      </div>
    </div>
  );
}
