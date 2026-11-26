// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import { describe, expect, it, vi } from "vitest";
import { AccountsError } from "../../../src/api/account";
import { McpAccountsApi, type ToolCaller } from "../../../src/api/mcp/mcp-accounts-api";

const WIRE = { name: "Perso", environment: "sandbox", read_only: true, is_default: true };
const ACCOUNT = { name: "Perso", environment: "sandbox", readOnly: true, isDefault: true };

function caller(result: Awaited<ReturnType<ToolCaller["callServerTool"]>>) {
  return { callServerTool: vi.fn().mockResolvedValue(result) };
}

describe("McpAccountsApi", () => {
  it("lists the accounts", async () => {
    const fake = caller({ structuredContent: { accounts: [WIRE] } });

    await expect(new McpAccountsApi(fake).list()).resolves.toEqual([ACCOUNT]);
    expect(fake.callServerTool).toHaveBeenCalledWith({ name: "app_list_accounts", arguments: {} });
  });

  it("adds an account with its token", async () => {
    const fake = caller({ structuredContent: { account: WIRE, username: "ada" } });

    const verified = await new McpAccountsApi(fake).add(
      { name: "Perso", environment: "sandbox", readOnly: true },
      "pat_0123456789abcdef",
    );

    expect(verified).toEqual({ account: ACCOUNT, username: "ada" });
    expect(fake.callServerTool).toHaveBeenCalledWith({
      name: "app_add_account",
      arguments: {
        name: "Perso",
        environment: "sandbox",
        read_only: true,
        token: "pat_0123456789abcdef",
      },
    });
  });

  it("sends only the requested changes", async () => {
    const fake = caller({ structuredContent: { account: WIRE } });
    const api = new McpAccountsApi(fake);

    await api.update("Perso", { newName: "Home" });
    await api.update("Perso", { readOnly: false, makeDefault: true });

    expect(fake.callServerTool.mock.calls.map((call) => call[0] as unknown)).toEqual([
      { name: "app_update_account", arguments: { name: "Perso", new_name: "Home" } },
      {
        name: "app_update_account",
        arguments: { name: "Perso", read_only: false, make_default: true },
      },
    ]);
  });

  it("replaces a token, changes the environment and removes", async () => {
    const fake = caller({ structuredContent: { account: WIRE, username: "ada" } });
    const api = new McpAccountsApi(fake);

    await api.replaceToken("Perso", "t".repeat(16));
    await api.changeEnvironment("Perso", "production", "t".repeat(16));
    await api.remove("Perso");

    expect(
      fake.callServerTool.mock.calls.map((call) => (call[0] as { name: string }).name),
    ).toEqual([
      "app_replace_account_token",
      "app_change_account_environment",
      "app_remove_account",
    ]);
  });

  it("turns tool errors into the server message", async () => {
    const fake = caller({
      isError: true,
      content: [{ type: "image" }, { type: "text", text: "Gandi refused the token" }],
    });

    await expect(new McpAccountsApi(fake).list()).rejects.toEqual(
      new AccountsError("Gandi refused the token"),
    );
  });

  it("handles results without data or text", async () => {
    await expect(new McpAccountsApi(caller({ content: [] })).list()).rejects.toEqual(
      new AccountsError(""),
    );
    await expect(new McpAccountsApi(caller({})).list()).rejects.toBeInstanceOf(AccountsError);
  });

  it("turns transport failures into errors", async () => {
    const failing = { callServerTool: vi.fn().mockRejectedValue(new Error("disconnected")) };
    const odd = { callServerTool: vi.fn().mockRejectedValue("boom") };

    await expect(new McpAccountsApi(failing).list()).rejects.toEqual(
      new AccountsError("disconnected"),
    );
    await expect(new McpAccountsApi(odd).list()).rejects.toEqual(new AccountsError("boom"));
  });
});
