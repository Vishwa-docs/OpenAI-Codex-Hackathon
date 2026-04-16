import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ProjectShell } from "@/components/project-shell";

vi.mock("next/navigation", () => ({
  usePathname: () => "/projects/atlas-inventory/providers"
}));

describe("ProjectShell", () => {
  it("renders project-specific copy from props", () => {
    render(<ProjectShell projectId="atlas-inventory" projectName="Atlas inventory platform" clientName="Atlas Logistics" />);

    expect(screen.getByText("Atlas Logistics")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Atlas inventory platform" })).toBeInTheDocument();
    expect(screen.getByText("Workspace ready")).toBeInTheDocument();
  });
});
