import { describe, expect, it, vi, afterEach } from "vitest";
import { BackendUnavailableError, loadProjectDataset } from "@/lib/api";
import { createMockProjectDataset } from "@/lib/mock-data";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("mock dataset helpers", () => {
  it("fails loudly when the marketing loaders cannot reach the API", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("network unavailable")));

    await expect(loadProjectDataset("legacycart")).rejects.toBeInstanceOf(BackendUnavailableError);
  });

  it("keeps the local snapshot deterministic", () => {
    const project = createMockProjectDataset("legacycart");

    expect(project.connectors[0].status).toBe("connected");
    expect(project.riskModel.overallRisk).toContain("High");
    expect(project.roadmap.waves).toHaveLength(3);
    expect(project.projectName).toBe("Retail commerce modernization assessment");
  });
});
