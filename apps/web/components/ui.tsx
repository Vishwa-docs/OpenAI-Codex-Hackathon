import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

export function Card({
  children,
  className
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("rounded-3xl border border-white/10 bg-white/[0.06] p-5 shadow-glow backdrop-blur", className)}>
      {children}
    </div>
  );
}

export function Badge({
  children,
  tone = "slate",
  className
}: {
  children: ReactNode;
  tone?: "slate" | "blue" | "green" | "amber" | "rose";
  className?: string;
}) {
  const tones = {
    slate: "bg-slate-200/10 text-slate-100 ring-slate-200/20",
    blue: "bg-sky-400/12 text-sky-100 ring-sky-300/25",
    green: "bg-emerald-400/12 text-emerald-100 ring-emerald-300/25",
    amber: "bg-amber-400/12 text-amber-100 ring-amber-300/25",
    rose: "bg-rose-400/12 text-rose-100 ring-rose-300/25"
  } as const;

  return (
    <span className={cn("inline-flex items-center rounded-full px-3 py-1 text-xs font-medium ring-1", tones[tone], className)}>
      {children}
    </span>
  );
}

export function MetricCard({
  label,
  value,
  detail,
  trend
}: {
  label: string;
  value: string;
  detail: string;
  trend?: string;
}) {
  return (
    <Card className="min-h-[150px]">
      <p className="text-xs uppercase tracking-[0.28em] text-slate-300">{label}</p>
      <div className="mt-4 flex items-end justify-between gap-4">
        <div>
          <div className="text-4xl font-semibold tracking-tight text-white">{value}</div>
          <p className="mt-2 max-w-xs text-sm leading-6 text-slate-300">{detail}</p>
        </div>
        {trend ? <Badge tone="green">{trend}</Badge> : null}
      </div>
    </Card>
  );
}

export function SectionHeader({
  eyebrow,
  title,
  description,
  action
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-4 border-b border-white/10 pb-4 md:flex-row md:items-end md:justify-between">
      <div className="max-w-3xl">
        {eyebrow ? <p className="text-xs font-semibold uppercase tracking-[0.28em] text-sky-200/80">{eyebrow}</p> : null}
        <h1 className="mt-2 text-2xl font-semibold text-white md:text-3xl">{title}</h1>
        {description ? <p className="mt-2 text-sm leading-6 text-slate-300">{description}</p> : null}
      </div>
      {action ? <div>{action}</div> : null}
    </div>
  );
}

export function PillList({ items }: { items: string[] }) {
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item) => (
        <Badge key={item} tone="slate">
          {item}
        </Badge>
      ))}
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <Card className="border-dashed border-white/20 bg-white/[0.04]">
      <h2 className="text-base font-medium text-white">{title}</h2>
      <p className="mt-2 text-sm leading-6 text-slate-300">{description}</p>
      {action ? <div className="mt-4">{action}</div> : null}
    </Card>
  );
}
