import { ProjectIntakeForm } from "@/components/project-intake-form";
import { BulletList } from "@/components/section-page";
import { Card, SectionHeader } from "@/components/ui";

const wizardSteps = [
  "Business context, migration goals, geography, and timelines",
  "Scale expectations, compliance requirements, and resiliency targets",
  "Source connection selection: local directory, GitHub, or Azure Repos",
  "Approval mode, evidence sensitivity, and connector safety posture"
];

export default function NewProjectPage() {
  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="New project"
        title="Seeded intake wizard"
        description="The MVP keeps intake explicit and structured so later agent runs stay evidence-backed, approval-aware, and safe by default."
      />
      <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <ProjectIntakeForm />
      </div>
      <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <Card className="space-y-4">
          <h2 className="text-lg font-medium text-white">Wizard steps</h2>
          <BulletList items={wizardSteps} />
        </Card>
        <Card className="space-y-4">
          <h2 className="text-lg font-medium text-white">Default posture</h2>
          <div className="space-y-3 text-sm leading-6 text-slate-300">
            <p>Read-only discovery is enabled for local directories.</p>
            <p>GitHub and Azure Repos remain connector-gated until credentials are supplied.</p>
            <p>AWS execution stays disabled until planning approval is explicitly granted.</p>
          </div>
        </Card>
      </div>
    </div>
  );
}
