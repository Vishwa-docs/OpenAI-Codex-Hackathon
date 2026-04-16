import { Card, SectionHeader } from "@/components/ui";
import Link from "next/link";

const steps = [
  "Open the LegacyCart project from the dashboard.",
  "Review the seeded findings, especially secrets, logging, and deployment risk.",
  "Compare AWS, GCP, and Azure from the provider tab.",
  "Inspect the cost, ROI, and risk screens for approval-ready framing.",
  "Ask the chat assistant to explain sequencing options.",
  "Export the executive PDF or switch into planning once the decision is clear."
];

const proofPoints = [
  { label: "Readiness", value: "52%", detail: "The project is intentionally viable but blocked." },
  { label: "Critical blockers", value: "4", detail: "Secrets, logging, IAM, and batch coupling all surface immediately." },
  { label: "Report packs", value: "8", detail: "Executive, technical, cost, risk, architecture, waves, rollback, and ops." }
];

export default function DemoPage() {
  return (
    <main className="mx-auto max-w-7xl px-6 pb-20 pt-14 lg:px-8">
      <SectionHeader
        eyebrow="Demo"
        title="A demo flow that shows the product in under five minutes."
        description="The seeded LegacyCart project is intentionally messy so the cockpit has useful evidence to surface immediately."
        action={
          <Link href="/projects/legacycart" className="rounded-full bg-sky-400 px-5 py-3 text-sm font-medium text-slate-950">
            Start demo
          </Link>
        }
      />
      <div className="mt-8 grid gap-4 lg:grid-cols-[1fr_0.8fr]">
        <Card className="space-y-4">
          <h2 className="text-lg font-medium text-white">Suggested presenter flow</h2>
          <div className="space-y-3">
            {steps.map((step, index) => (
              <div key={step} className="flex gap-4 rounded-2xl bg-white/5 px-4 py-3 text-sm leading-6 text-slate-300">
                <span className="font-semibold text-sky-200">{index + 1}</span>
                <span>{step}</span>
              </div>
            ))}
          </div>
        </Card>
        <Card className="space-y-3">
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Demo seed</p>
          <h2 className="text-2xl font-semibold text-white">LegacyCart</h2>
          <p className="text-sm leading-6 text-slate-300">
            A retail order-management monolith with hardcoded secrets, sensitive logs, a brittle CI chain, and shared file storage.
          </p>
          <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-4 text-sm leading-6 text-slate-300">
            It looks believable to technical and non-technical viewers because the cockpit surfaces both a concise recommendation and the underlying evidence trail.
          </div>
        </Card>
      </div>
      <div className="mt-8 grid gap-4 lg:grid-cols-3">
        {proofPoints.map((point) => (
          <Card key={point.label} className="space-y-2">
            <p className="text-xs uppercase tracking-[0.28em] text-slate-400">{point.label}</p>
            <p className="text-3xl font-semibold text-white">{point.value}</p>
            <p className="text-sm leading-6 text-slate-300">{point.detail}</p>
          </Card>
        ))}
      </div>
    </main>
  );
}
