import { afterEach, describe, expect, it, vi } from "vitest";
import { BackendUnavailableError, loadDashboardSummary, loadProjectDataset } from "@/lib/app-api";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("app api loaders", () => {
  it("fails loudly when the backend cannot be reached", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("network unavailable")));

    await expect(loadDashboardSummary()).rejects.toBeInstanceOf(BackendUnavailableError);
  });

  it("does not silently fall back to mock data in the app path", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("network unavailable")));

    await expect(loadProjectDataset("legacycart")).rejects.toMatchObject({
      sourcePath: expect.stringContaining("/projects/legacycart")
    });
  });
});
