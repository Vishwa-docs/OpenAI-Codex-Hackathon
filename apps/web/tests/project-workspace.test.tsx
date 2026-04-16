import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  CommandCenterPanel,
  DeploymentReadinessPanel,
  ExecutiveRibbon,
  MtcPipelinePanel,
  ObservabilityPanel,
  ReportCenterPanel
} from "@/components/project-workspace";
import { createMockProjectDataset } from "@/lib/mock-data";

describe("project workspace panels", () => {
  it("renders the executive ribbon for dual-audience navigation", () => {
    const project = createMockProjectDataset("legacycart");

    render(
      <ExecutiveRibbon
        overview={project.overview}
        costModel={project.costModel}
        riskModel={project.riskModel}
        approvals={project.approvals}
      />
    );

    expect(screen.getByText("Migration decision")).toBeInTheDocument();
    expect(screen.getByText("Defer until blockers are remediated")).toBeInTheDocument();
    expect(screen.getByText("Approval state")).toBeInTheDocument();
  });

  it("shows operator command center and report center details", () => {
    const project = createMockProjectDataset("legacycart");

    render(
      <>
        <CommandCenterPanel
          connectors={project.connectors}
          approvals={project.approvals}
          auditEvents={project.auditEvents}
          evaluation={project.evaluation}
        />
        <ReportCenterPanel artifacts={project.artifacts} reports={project.reports} exportFormats={project.exportFormats} />
        <MtcPipelinePanel mtcPipeline={project.mtcPipeline} />
        <ObservabilityPanel observability={project.observability} />
        <DeploymentReadinessPanel deploymentPlan={project.deploymentPlan} />
      </>
    );

    expect(screen.getByText("Command center")).toBeInTheDocument();
    expect(screen.getByText("Report center")).toBeInTheDocument();
    expect(screen.getByText("Executive Summary PDF")).toBeInTheDocument();
    expect(screen.getByText("MTC pipeline")).toBeInTheDocument();
    expect(screen.getByText("Agent observability")).toBeInTheDocument();
    expect(screen.getAllByText("Deployment readiness").length).toBeGreaterThan(0);
  });
});
