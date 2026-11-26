// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import type {
  Account,
  AccountChanges,
  AccountDraft,
  Environment,
  VerifiedAccount,
} from "./account";

/**
 * Account operations offered to the MCP App. Every operation rejects with an
 * `AccountsError` carrying a message for the user.
 */
export interface AccountsApi {
  list(): Promise<Account[]>;
  add(draft: AccountDraft, token: string): Promise<VerifiedAccount>;
  update(name: string, changes: AccountChanges): Promise<Account>;
  replaceToken(name: string, token: string): Promise<VerifiedAccount>;
  changeEnvironment(
    name: string,
    environment: Environment,
    token: string,
  ): Promise<VerifiedAccount>;
  remove(name: string): Promise<void>;
}
