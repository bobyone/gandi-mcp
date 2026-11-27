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
import type { Organization } from "../organization";
import type { PendingConfirmation } from "../pending-confirmation";
import { callTool, pendingOf, type ToolCaller } from "./tool-caller";

interface WireAccount {
  name: string;
  environment: Environment;
  read_only: boolean;
  is_default: boolean;
  removal_pending?: boolean;
  paying_organization?: string | null;
}

/** An organization as Gandi describes it: untrusted, so every field is checked. */
interface WireOrganization {
  id: unknown;
  name: unknown;
  type: unknown;
}

function account(wire: WireAccount): Account {
  return {
    name: wire.name,
    environment: wire.environment,
    readOnly: wire.read_only,
    isDefault: wire.is_default,
    removalPending: wire.removal_pending === true,
    payingOrganization: wire.paying_organization ?? null,
  };
}

/**
 * Calls the app-only account tools of the gandi-mcp server through the host, and the
 * organization tools shared with the model (ADR 12).
 */
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

  async update(
    name: string,
    changes: AccountChanges,
    confirmationId?: string,
  ): Promise<Account | PendingConfirmation> {
    const result = await this.call("app_update_account", {
      name,
      ...(confirmationId !== undefined && { confirmation_id: confirmationId }),
      ...(changes.newName !== undefined && { new_name: changes.newName }),
      ...(changes.readOnly !== undefined && { read_only: changes.readOnly }),
      ...(changes.makeDefault !== undefined && { make_default: changes.makeDefault }),
    });
    return pendingOf(result) ?? account(result.account as WireAccount);
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

  async remove(name: string, confirmationId?: string): Promise<PendingConfirmation | null> {
    return pendingOf(
      await this.call("app_remove_account", {
        name,
        ...(confirmationId !== undefined && { confirmation_id: confirmationId }),
      }),
    );
  }

  private verified(result: Record<string, unknown>): VerifiedAccount {
    return { account: account(result.account as WireAccount), username: String(result.username) };
  }

  async organizations(name: string): Promise<Organization[]> {
    const result = await this.call("list_organizations", { account: name });
    const items = Array.isArray(result.untrusted_data)
      ? (result.untrusted_data as WireOrganization[])
      : [];
    return items.map((item) => ({
      id: String(item.id),
      name: String(item.name),
      type: String(item.type),
    }));
  }

  async setPayingOrganization(name: string, organizationId: string | null): Promise<Account> {
    const result = await this.call("set_paying_organization", {
      account: name,
      ...(organizationId !== null && { organization_id: organizationId }),
    });
    return account(result.account as WireAccount);
  }

  private call(name: string, args: Record<string, unknown>): Promise<Record<string, unknown>> {
    return callTool(this.caller, name, args, (message) => new AccountsError(message));
  }
}
