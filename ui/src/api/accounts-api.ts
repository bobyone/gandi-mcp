// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import type {
  Account,
  AccountChanges,
  AccountDraft,
  Environment,
  PendingConfirmation,
  VerifiedAccount,
} from "./account";

/**
 * Account operations offered to the MCP App. Every operation rejects with an
 * `AccountsError` carrying a message for the user. A confirmation given in the App
 * itself is not enough: the server asks the user again, outside the App.
 */
export interface AccountsApi {
  list(): Promise<Account[]>;
  add(draft: AccountDraft, token: string): Promise<VerifiedAccount>;
  /** Allowing writes is confirmed by the user: the change may come back pending. */
  update(
    name: string,
    changes: AccountChanges,
    confirmationId?: string,
  ): Promise<Account | PendingConfirmation>;
  replaceToken(name: string, token: string): Promise<VerifiedAccount>;
  changeEnvironment(
    name: string,
    environment: Environment,
    token: string,
  ): Promise<VerifiedAccount>;
  /** Removing is confirmed by the user: it may come back pending. */
  remove(name: string, confirmationId?: string): Promise<PendingConfirmation | null>;
}
