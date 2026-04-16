import { Badge, SectionHeader } from "@/components/ui";
import Link from "next/link";

const productFrames = [
  {
    label: "Public SaaS surface",
    title: "The website should feel like Apple or Microsoft: clear, confident, and easy to buy into.",
    body: "This layer exists to explain the product, the workflow, and the category. It should position the system like a real platform rather than a dev tool stitched together for demos."
  },
  {
    label: "Local AI runtime",
    title: "The actual intelligence runs locally where evidence, code, and approvals already exist.",
    body: "That keeps the serious work grounded in the real environment while preserving the trust model around code, credentials, and internal operating context."
  },
  {
    label: "Operator dashboard",
    title: "After handoff, everything happens through a dashboard designed for decisions.",
    body: "The MTC pipeline should stop feeling like a script and start feeling like a workbench with questions, reports, inferences, approvals, and drill-down detail."
  }
];

const dashboardModes = [
  "Ask people for missing business, compliance, or delivery context before the next run advances",
  "Present AI-generated inferences with confidence, rationale, and clear evidence links",
  "Open executive and technical reports without leaving the workspace",
  "Move between project overview, findings, scenarios, approvals, connectors, and artifacts from one place",
  "Turn outputs into action by making the next human decision obvious"
];

const principles = [
  {
    title: "One product story",
    body: "Marketing pages should communicate why the platform matters, how it works, and what buyers should expect from the experience."
  },
  {
    title: "One execution posture",
    body: "The AI runtime should stay local-first and operator-safe, with evidence, credentials, and approval gates close to the real environment."
  },
  {
    title: "One interaction surface",
    body: "Once the run begins, the dashboard should become the default place for questions, details, reports, and next actions."
  }
];

export default function ProductPage() {
  return (
    <main className="mx-auto max-w-7xl px-6 pb-24 pt-14 lg:px-8">
      <SectionHeader
        eyebrow="Product"
        title="A public product story outside. A local AI workbench inside."
        description="Cloud Migration Cockpit is not just a scanner with nice charts. It is a product surface for buyers, a local runtime for AI work, and a dashboard for every meaningful interaction with the MTC pipeline."
        action={
          <Link href="/projects/legacycart" className="rounded-full bg-sky-400 px-5 py-3 text-sm font-medium text-slate-950">
            Open dashboard
          </Link>
        }
      />
      <section className="mt-10 grid gap-8 lg:grid-cols-3">
        {productFrames.map((frame) => (
          <div key={frame.label} className="border-t border-white/10 pt-5">
            <p className="text-xs uppercase tracking-[0.28em] text-sky-200/80">{frame.label}</p>
            <h2 className="mt-3 text-3xl font-semibold text-white">{frame.title}</h2>
            <p className="mt-3 text-sm leading-7 text-slate-300">{frame.body}</p>
          </div>
        ))}
      </section>

      <section className="mt-16 overflow-hidden rounded-[2.4rem] border border-white/10 bg-[linear-gradient(135deg,rgba(56,189,248,0.08),rgba(15,23,42,0.7))] p-8 lg:p-10">
        <div className="grid gap-8 lg:grid-cols-[0.95fr_1.05fr] lg:items-start">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Dashboard behavior</p>
            <h2 className="mt-4 text-4xl font-semibold text-white">The dashboard should feel like an AI partner with a memory, not a static report viewer.</h2>
            <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-300">
              That means the UI has to do more than show output. It has to ask for answers when context is missing,
              present inferences clearly, surface reports without ceremony, and make next decisions easy for both
              technical and non-technical people.
            </p>
          </div>
          <div className="grid gap-3">
            {dashboardModes.map((item) => (
              <div key={item} className="rounded-[1.5rem] border border-white/10 bg-white/[0.05] px-4 py-4 text-sm leading-6 text-slate-200">
                {item}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mt-16 grid gap-8 lg:grid-cols-[1.05fr_0.95fr]">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Design principles</p>
          <h2 className="mt-4 text-4xl font-semibold text-white">A clean split creates a better product on both sides.</h2>
        </div>
        <div className="grid gap-5">
          {principles.map((principle) => (
            <div key={principle.title} className="border-b border-white/10 pb-5 last:border-b-0 last:pb-0">
              <div className="flex items-center gap-3">
                <Badge tone="blue">{principle.title}</Badge>
              </div>
              <p className="mt-3 text-sm leading-7 text-slate-300">{principle.body}</p>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
