import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ProjectIntakeForm } from "@/components/project-intake-form";

const push = vi.fn();
const refresh = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push,
    refresh,
  }),
}));

afterEach(() => {
  vi.restoreAllMocks();
  push.mockReset();
  refresh.mockReset();
});

describe("ProjectIntakeForm", () => {
  it("creates a project through the API and navigates to the project page", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          id: "phoenix-modernization",
          name: "Phoenix Modernization",
          clientName: "Phoenix Health",
          readinessScore: 0,
          migrationDecision: "Intake in progress",
          confidence: 0,
          phase: "Intake",
          status: "Draft intake",
          recommendedProvider: "Pending",
        }),
        { status: 201 },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    render(<ProjectIntakeForm workspaceId="workspace-demo" />);

    fireEvent.change(screen.getByPlaceholderText(/Northstar checkout modernization/i), {
      target: { value: "Phoenix Modernization" },
    });
    fireEvent.change(screen.getByPlaceholderText(/Northstar Retail/i), {
      target: { value: "Phoenix Health" },
    });
    fireEvent.change(screen.getByPlaceholderText(/On-prem Java monolith/i), {
      target: { value: "Legacy Java stack" },
    });
    fireEvent.change(screen.getByPlaceholderText(/AWS landing zone/i), {
      target: { value: "AWS modern target" },
    });
    fireEvent.change(screen.getByPlaceholderText(/Revenue-critical commerce flow/i), {
      target: { value: "Healthcare orchestration workload" },
    });
    fireEvent.change(screen.getByPlaceholderText(/Taylor Reed/i), {
      target: { value: "Mia Chen" },
    });
    fireEvent.change(screen.getByPlaceholderText(/PCI DSS, SOC 2, HIPAA/i), {
      target: { value: "HIPAA, ISO 27001" },
    });

    fireEvent.click(screen.getByRole("button", { name: /Create project/i }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(1);
    });
    expect(push).toHaveBeenCalledWith("/projects/phoenix-modernization");
    expect(refresh).toHaveBeenCalled();
  });
});
