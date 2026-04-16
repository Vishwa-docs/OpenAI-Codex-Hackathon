import { BulletList } from "@/components/section-page";
import { Card, MetricCard, SectionHeader } from "@/components/ui";
import { loadProjectDataset } from "@/lib/app-api";

export default async function CostRoiPage({
  params
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  const project = await loadProjectDataset(projectId);

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Cost and ROI"
        title="Financial view of the migration path"
        description="The cost model compares current-state run rate against the proposed target and makes its assumptions visible."
      />
      <div className="grid gap-4 xl:grid-cols-4">
        <MetricCard label="Current monthly run rate" value={`$${project.costModel.currentMonthlyRunRate.toLocaleString()}`} detail="Legacy operations, storage, and database costs." />
        <MetricCard label="Target monthly run rate" value={`$${project.costModel.targetMonthlyRunRate.toLocaleString()}`} detail="Projected steady-state cloud operations." />
        <MetricCard label="One-time migration cost" value={`$${project.costModel.migrationOneTimeCost.toLocaleString()}`} detail="Remediation, platform setup, and cutover work." />
        <MetricCard label="Estimated payback" value={`${project.costModel.estimatedPaybackMonths} mo`} detail={`ROI ${project.costModel.roiPercent}%`} />
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <Card className="space-y-4">
          <h2 className="text-lg font-medium text-white">Driver breakdown</h2>
          <div className="space-y-3">
            {project.costModel.driverBreakdown.map((driver) => (
              <div key={driver.label} className="rounded-2xl bg-white/5 p-4">
                <div className="flex items-center justify-between gap-4 text-sm text-white">
                  <span>{driver.label}</span>
                  <span>
                    ${driver.current.toLocaleString()} → ${driver.target.toLocaleString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Card>
        <Card className="space-y-4">
          <h2 className="text-lg font-medium text-white">Assumptions</h2>
          <BulletList items={project.costModel.assumptions} />
        </Card>
      </div>
    </div>
  );
}
