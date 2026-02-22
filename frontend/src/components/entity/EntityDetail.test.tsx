import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";

import "@/i18n";

vi.mock("@/api/client", () => ({
  getEntity: vi.fn(),
}));

import { getEntity } from "@/api/client";
import { EntityDetail } from "./EntityDetail";

const mockGetEntity = vi.mocked(getEntity);

const sampleEntity = {
  id: "e1",
  name: "João Silva",
  type: "person",
  document: "***.***.***-34",
  properties: { role: "Diretor", city: "São Paulo" },
  sources: ["TSE", "CNPJ"],
};

describe("EntityDetail", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetEntity.mockResolvedValue(sampleEntity);
  });

  it("returns null when entityId is null", () => {
    const { container } = render(
      <EntityDetail entityId={null} onClose={vi.fn()} />,
    );
    expect(container.innerHTML).toBe("");
  });

  it("shows loading state", async () => {
    let resolve: (v: unknown) => void;
    const pending = new Promise((r) => {
      resolve = r;
    });
    mockGetEntity.mockReturnValueOnce(pending as ReturnType<typeof getEntity>);

    render(<EntityDetail entityId="e1" onClose={vi.fn()} />);

    expect(screen.getByText(/carregando/i)).toBeInTheDocument();

    await act(async () => {
      resolve!(sampleEntity);
    });
  });

  it("shows entity details after fetch", async () => {
    render(<EntityDetail entityId="e1" onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("João Silva")).toBeInTheDocument();
    });
    expect(screen.getByText("Pessoa")).toBeInTheDocument();
    expect(screen.getByText("***.***.***-34")).toBeInTheDocument();
  });

  it("shows properties", async () => {
    render(<EntityDetail entityId="e1" onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("role")).toBeInTheDocument();
      expect(screen.getByText("Diretor")).toBeInTheDocument();
      expect(screen.getByText("city")).toBeInTheDocument();
      expect(screen.getByText("São Paulo")).toBeInTheDocument();
    });
  });

  it("shows source badges", async () => {
    render(<EntityDetail entityId="e1" onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("TSE")).toBeInTheDocument();
      expect(screen.getByText("CNPJ")).toBeInTheDocument();
    });
  });

  it("close button calls onClose", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(<EntityDetail entityId="e1" onClose={onClose} />);

    await waitFor(() => {
      expect(screen.getByText("João Silva")).toBeInTheDocument();
    });

    await user.click(screen.getByText("\u00d7"));
    expect(onClose).toHaveBeenCalledOnce();
  });
});
