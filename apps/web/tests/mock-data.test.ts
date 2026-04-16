import { describe, expect, it, vi, afterEach } from "vitest";
import { createMockProjectDataset } from "@/lib/mock-data";
import { loadProjectDataset } from "@/lib/api";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("mock data fallback", () => {
  it("returns the seeded project snapshot when the API is unavailable", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("network unavailable")));

    const project = await loadProjectDataset("legacycart");

    expect(project.projectName).toBe("LegacyCart migration assessment");
    expect(project.overview.readinessScore).toBe(52);
    expect(project.findings).toHaveLength(4);
  });

  it("keeps the seeded snapshot deterministic", () => {
    const project = createMockProjectDataset("legacycart");

    expect(project.connectors[0].status).toBe("connected");
    expect(project.riskModel.overallRisk).toContain("High");
    expect(project.roadmap.waves).toHaveLength(3);
  });
});
