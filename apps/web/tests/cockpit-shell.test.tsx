import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CockpitShell } from "@/components/cockpit-shell";

vi.mock("next/navigation", () => ({
  usePathname: () => "/dashboard"
}));

describe("CockpitShell", () => {
  it("shows neutral workspace chrome instead of a hardcoded legacy project", () => {
    render(
      <CockpitShell session={null}>
        <div>Content</div>
      </CockpitShell>
    );

    expect(screen.getByText("Workspace overview")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open projects" })).toBeInTheDocument();
    expect(screen.queryByText("LegacyCart")).not.toBeInTheDocument();
  });
});
