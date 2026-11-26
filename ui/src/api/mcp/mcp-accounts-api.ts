// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import type {
  Account,
  AccountChanges,
  AccountDraft,
  Environment,
  VerifiedAccount,
} from "../account";
import { AccountsError } from "../account";
import type { AccountsApi } from "../accounts-api";

/** The part of the MCP App connection used to call the app-only tools. */
export interface ToolCaller {
  callServerTool(params: { name: string; arguments: Record<string, unknown> }): Promise<{
    isError?: boolean | undefined;
    structuredContent?: unknown;
    content?: unknown[] | undefined;
  }>;
}

interface WireAccount {
  name: string;
  environment: Environment;
  read_only: boolean;
  is_default: boolean;
}

function account(wire: WireAccount): Account {
  return {
    name: wire.name,
    environment: wire.environment,
    readOnly: wire.read_only,
    isDefault: wire.is_default,
  };
}

function errorText(content: unknown[] | undefined): string {
  const block = content?.find(
    (item): item is { type: "text"; text: string } =>
      typeof item === "object" &&
      item !== null &&
      (item as { type?: unknown }).type === "text" &&
      typeof (item as { text?: unknown }).text === "string",
  );
  return block?.text ?? "";
}

/** Calls the app-only tools of the gandi-mcp server through the host. */
export class McpAccountsApi implements AccountsApi {
  constructor(private readonly caller: ToolCaller) {}

  async list(): Promise<Account[]> {
    const result = await this.call("app_list_accounts", {});
    return (result.accounts as WireAccount[]).map(account);
  }

  async add(draft: AccountDraft, token: string): Promise<VerifiedAccount> {
    return this.verified(
      await this.call("app_add_account", {
        name: draft.name,
        environment: draft.environment,
        read_only: draft.readOnly,
        token,
      }),
    );
  }

  async update(name: string, changes: AccountChanges): Promise<Account> {
    const result = await this.call("app_update_account", {
      name,
      ...(changes.newName !== undefined && { new_name: changes.newName }),
      ...(changes.readOnly !== undefined && { read_only: changes.readOnly }),
      ...(changes.makeDefault !== undefined && { make_default: changes.makeDefault }),
    });
    return account(result.account as WireAccount);
  }

  async replaceToken(name: string, token: string): Promise<VerifiedAccount> {
    return this.verified(await this.call("app_replace_account_token", { name, token }));
  }

  async changeEnvironment(
    name: string,
    environment: Environment,
    token: string,
  ): Promise<VerifiedAccount> {
    return this.verified(
      await this.call("app_change_account_environment", { name, environment, token }),
    );
  }

  async remove(name: string): Promise<void> {
    await this.call("app_remove_account", { name });
  }

  private verified(result: Record<string, unknown>): VerifiedAccount {
    return { account: account(result.account as WireAccount), username: String(result.username) };
  }

  private async call(
    name: string,
    args: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    let result;
    try {
      result = await this.caller.callServerTool({ name, arguments: args });
    } catch (error) {
      throw new AccountsError(error instanceof Error ? error.message : String(error));
    }
    const data = result.structuredContent;
    if (result.isError === true || typeof data !== "object" || data === null) {
      throw new AccountsError(errorText(result.content));
    }
    return data as Record<string, unknown>;
  }
}
