import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { FindingsList } from "@/components/section-page";
import { createMockProjectDataset } from "@/lib/mock-data";

describe("FindingsList", () => {
  it("renders evidence-backed findings for the cockpit", () => {
    const project = createMockProjectDataset();

    render(<FindingsList findings={project.findings} />);

    expect(screen.getByText("Production database credentials are hardcoded")).toBeInTheDocument();
    expect(screen.getByText("Sensitive identity data is present in logs")).toBeInTheDocument();
    expect(screen.getByText("demo-systems/legacycart/backend/src/main/resources/application-prod.yml")).toBeInTheDocument();
  });
});
