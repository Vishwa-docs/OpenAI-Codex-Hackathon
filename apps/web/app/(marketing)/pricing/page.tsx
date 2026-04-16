import { Badge, Card, SectionHeader } from "@/components/ui";
import { getDesktopDownloadUrl } from "@/lib/runtime";
import Link from "next/link";

const plans = [
  {
    name: "Pilot",
    hint: "For one migration engagement or internal proof point",
    price: "Custom",
    features: ["Public SaaS product surface", "One dashboard workspace", "Local AI runtime setup", "Reports and approvals"]
  },
  {
    name: "Consultancy",
    hint: "For MSP and delivery teams running multiple workstreams",
    price: "Custom",
    features: ["Multi-project dashboard", "Question and inference workflows", "Scenario and report center", "Connector governance"]
  },
  {
    name: "Enterprise",
    hint: "For migration offices standardizing internal programs",
    price: "Talk to us",
    features: ["Platform rollout support", "Local runtime controls", "Advanced governance and approvals", "Custom workflow extensions"]
  }
];

export default function PricingPage() {
  return (
    <main className="mx-auto max-w-7xl px-6 pb-20 pt-14 lg:px-8">
      <SectionHeader
        eyebrow="Pricing"
        title="Commercial framing for a product site, not a deployment checklist."
        description="The public pricing surface should describe how teams adopt the platform, while the actual AI runtime and MTC work happen after onboarding inside the dashboard."
        action={
          <Link href={getDesktopDownloadUrl()} className="rounded-full border border-white/15 px-5 py-3 text-sm font-medium text-white">
            Download macOS app
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
