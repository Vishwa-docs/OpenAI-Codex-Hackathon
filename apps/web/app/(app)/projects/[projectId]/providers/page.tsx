import { EvidenceList, ProviderCards } from "@/components/section-page";
import { SectionHeader } from "@/components/ui";
import { loadProjectDataset } from "@/lib/api";

export default async function ProvidersPage({
  params
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  const project = await loadProjectDataset(projectId);
  const leadingEvidence = project.providers[0]?.evidence ?? project.evidence.slice(0, 3);

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Provider comparison"
        title="AWS, GCP, and Azure side-by-side"
        description="The seeded recommendation compares provider fit against the workload’s constraints, operating model, and future execution roadmap."
      />
      <ProviderCards providers={project.providers} />
      <EvidenceList evidence={leadingEvidence} title="Evidence informing the leading provider choice" />
    </div>
  );
}
