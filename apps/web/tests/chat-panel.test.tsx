import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ChatPanel } from "@/components/chat-panel";

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    replace: vi.fn(),
    refresh: vi.fn(),
  }),
}));

afterEach(() => {
  vi.restoreAllMocks();
});

describe("ChatPanel", () => {
  it("posts through the API and refreshes the thread", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "chat-003" }), { status: 201 }))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify([
            {
              id: "chat-001",
              author: "Mia Chen",
              role: "human",
              createdAt: "2026-04-16T10:30:00Z",
              content: "What is the safest path?",
            },
            {
              id: "chat-002",
              author: "Cockpit Assistant",
              role: "ai",
              createdAt: "2026-04-16T10:30:10Z",
              content: "Defer execution until the highest-risk blockers are remediated.",
            },
          ]),
          { status: 200 },
        ),
      );

    vi.stubGlobal("fetch", fetchMock);

    render(
      <ChatPanel
        projectId="legacycart"
        projectName="Retail commerce modernization assessment"
        messages={[
          {
            id: "chat-000",
            author: "Cockpit Assistant",
            role: "ai",
            createdAt: "2026-04-16T10:29:00Z",
            content: "I am ready to answer from the dossier.",
          },
        ]}
      />,
    );

    fireEvent.change(screen.getByPlaceholderText(/Ask about migration sequencing/i), {
      target: { value: "Should we move the database first?" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Send to cockpit assistant/i }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(2);
    });
    expect(await screen.findByText(/Defer execution until the highest-risk blockers are remediated./i)).toBeInTheDocument();
  });
});
