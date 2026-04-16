import { Badge, Card, SectionHeader } from "@/components/ui";
import Link from "next/link";

const plans = [
  { name: "Pilot", hint: "For a single assessment engagement", price: "Custom", features: ["One workspace", "Seeded evaluation views", "PDF export", "Local stack for demos"] },
  { name: "Consultancy", hint: "For an MSP delivery team", price: "Custom", features: ["Multi-project cockpit", "Approval gates", "Connector registry", "Scenario and report center"] },
  { name: "Enterprise", hint: "For internal migration offices", price: "Talk to us", features: ["Advanced tenancy", "Execution adapters", "Custom eval packs", "Control-plane extensions"] }
];

export default function PricingPage() {
  return (
    <main className="mx-auto max-w-7xl px-6 pb-20 pt-14 lg:px-8">
      <SectionHeader
        eyebrow="Pricing"
        title="Placeholder pricing with room for the real commercial model."
        description="The MVP keeps pricing simple so the product can focus on proving value and earning the next implementation step."
        action={
          <Link href="/demo" className="rounded-full border border-white/15 px-5 py-3 text-sm font-medium text-white">
            Book demo
          </Link>
        }
      />
      <div className="mt-8 grid gap-4 lg:grid-cols-3">
        {plans.map((plan) => (
          <Card key={plan.name} className="space-y-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold text-white">{plan.name}</h2>
                <p className="mt-1 text-sm text-slate-300">{plan.hint}</p>
              </div>
              <Badge tone="blue">{plan.price}</Badge>
            </div>
            <ul className="space-y-2 text-sm leading-6 text-slate-300">
              {plan.features.map((feature) => (
                <li key={feature} className="rounded-2xl bg-white/5 px-4 py-3">
                  {feature}
                </li>
              ))}
            </ul>
          </Card>
        ))}
      </div>
    </main>
  );
}
