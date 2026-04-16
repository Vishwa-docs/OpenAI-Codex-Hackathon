import { ProjectIntakeForm } from "@/components/project-intake-form";
import { BulletList } from "@/components/section-page";
import { Card, SectionHeader } from "@/components/ui";

const wizardSteps = [
  "Paste the real source path or repository URL you want the swarm to analyze",
  "Start a read-only scan and capture evidence, findings, questions, and platform fit",
  "Review the generated documents, costs, benefits, requirements, and flagged repo issues",
  "Approve the next execution step only after the questions and plan are finalized"
];

export default function NewProjectPage() {
  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="New project"
        title="Judge intake workspace"
        description="This intake starts empty on purpose. Paste a real project path, let the swarm analyze it, and keep the workflow approval-aware from the first run."
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
            <p>Read-only discovery is enabled for local paths.</p>
            <p>GitHub and Azure Repos remain connector-gated until credentials are supplied.</p>
            <p>Execution stays disabled until the analysis questions are resolved and planning approval is explicitly granted.</p>
          </div>
        </Card>
      </div>
    </div>
  );
}
