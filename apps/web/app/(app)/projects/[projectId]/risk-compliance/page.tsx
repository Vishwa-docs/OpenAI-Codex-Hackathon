import { BulletList } from "@/components/section-page";
import { Card, MetricCard, PillList, SectionHeader } from "@/components/ui";
import { loadProjectDataset } from "@/lib/api";

export default async function RiskCompliancePage({
  params
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  const project = await loadProjectDataset(projectId);

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Risk and compliance"
        title="Operational, security, and governance posture"
        description="The cockpit exposes risk domains, controls, and compliance notes instead of burying them in a technical appendix."
      />
      <div className="grid gap-4 xl:grid-cols-3">
        <MetricCard label="Overall risk" value={project.riskModel.overallRisk} detail="Current readiness before remediation." />
        <MetricCard label="RPO target" value={project.riskModel.rpo} detail="Seeded transactional recovery posture." />
        <MetricCard label="RTO target" value={project.riskModel.rto} detail="Expected recovery window for order intake." />
      </div>
      <div className="grid gap-4 xl:grid-cols-3">
        <Card className="space-y-4">
          <h2 className="text-lg font-medium text-white">Compliance notes</h2>
          <PillList items={project.riskModel.complianceNotes} />
        </Card>
        <Card className="space-y-4">
          <h2 className="text-lg font-medium text-white">Open issues</h2>
          <BulletList items={project.riskModel.openIssues} />
        </Card>
        <Card className="space-y-4">
          <h2 className="text-lg font-medium text-white">Recommended controls</h2>
          <BulletList items={project.riskModel.recommendedControls} />
        </Card>
      </div>
    </div>
  );
}
