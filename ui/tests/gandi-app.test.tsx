// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import type { App } from "@modelcontextprotocol/ext-apps";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { GandiApp } from "../src/gandi-app";

function fakeApp(locale: string, theme: "light" | "dark"): App {
  return {
    getHostContext: () => ({ locale, theme }),
    callServerTool: vi.fn().mockResolvedValue({ structuredContent: { accounts: [] } }),
    onhostcontextchanged: undefined,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  } as unknown as App;
}

describe("GandiApp", () => {
  it("waits for the connection", async () => {
    render(<GandiApp app={null} error={null} />);

    expect(await screen.findByRole("status")).toHaveTextContent("Connecting to the client");
  });

  it("explains a connection failure", async () => {
    render(<GandiApp app={null} error={new Error("no host")} />);

    expect(await screen.findByRole("alert")).toHaveTextContent("could not connect");
  });

  it("follows the language and theme of the host", async () => {
    render(<GandiApp app={fakeApp("fr-FR", "dark")} error={null} />);

    expect(await screen.findByRole("heading", { level: 1 })).toBeInTheDocument();
    expect(document.documentElement.lang).toBe("fr");
    expect(document.documentElement.dataset.bsTheme).toBe("dark");
  });

  it("switches between the accounts and the domains", async () => {
    render(<GandiApp app={fakeApp("en", "light")} error={null} />);
    const user = userEvent.setup();

    expect(await screen.findByRole("heading", { name: "Gandi accounts" })).toBeInTheDocument();
    await user.click(screen.getByRole("tab", { name: "Domains" }));

    expect(await screen.findByRole("heading", { name: "Gandi domains" })).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.queryByRole("heading", { name: "Gandi accounts" })).not.toBeInTheDocument();
    });
  });
});
