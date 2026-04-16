import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ProjectIntakeForm } from "@/components/project-intake-form";

const { push, refresh, createWorkspaceProject } = vi.hoisted(() => ({
  push: vi.fn(),
  refresh: vi.fn(),
  createWorkspaceProject: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push,
    refresh,
  }),
}));

vi.mock("@/lib/app-api", () => ({
  DEFAULT_WORKSPACE_ID: "workspace-judge",
  createWorkspaceProject,
}));

describe("project intake form", () => {
  it("submits the intake and routes into the new project workspace", async () => {
    createWorkspaceProject.mockResolvedValue({ id: "judge-ready-app" });
    render(<ProjectIntakeForm />);

    expect(screen.getByLabelText("Local path or GitHub URL")).toBeInTheDocument();
    expect(screen.getByLabelText("Expected users")).toHaveValue(25);

    fireEvent.change(screen.getByLabelText("Local path or GitHub URL"), {
      target: { value: "/Users/judge/projects/judge-ready-app" },
    });
    fireEvent.change(screen.getByLabelText("Expected users"), { target: { value: "120" } });
    fireEvent.click(screen.getByRole("button", { name: "Start analysis" }));

    await waitFor(() => {
      expect(createWorkspaceProject).toHaveBeenCalledWith(
        "workspace-judge",
        expect.objectContaining({
          sourceKind: "local_path",
          sourceTarget: "/Users/judge/projects/judge-ready-app",
          expectedUsers: 120,
        }),
      );
      expect(push).toHaveBeenCalledWith("/projects/judge-ready-app");
      expect(refresh).toHaveBeenCalled();
    });
  });
});
