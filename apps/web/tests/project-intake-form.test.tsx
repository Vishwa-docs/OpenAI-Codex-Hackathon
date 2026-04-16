import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ProjectIntakeForm } from "@/components/project-intake-form";

describe("project intake form", () => {
  it("collects source and scale inputs for founder-friendly intake", () => {
    render(<ProjectIntakeForm />);

    expect(screen.getByLabelText("Local path or GitHub URL")).toBeInTheDocument();
    expect(screen.getByLabelText("Expected users")).toHaveValue(25);

    fireEvent.change(screen.getByLabelText("Expected users"), { target: { value: "120" } });

    expect(screen.getByDisplayValue("120")).toBeInTheDocument();
    expect(screen.getByText("Recommended path for the current answers")).toBeInTheDocument();
  });
});
