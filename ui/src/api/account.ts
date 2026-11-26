// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
/** Values exchanged with the server about accounts; never a token in a result. */

export type Environment = "production" | "sandbox";

export interface Account {
  readonly name: string;
  readonly environment: Environment;
  readonly readOnly: boolean;
  readonly isDefault: boolean;
  /** A removal was interrupted: removing the account again completes it. */
  readonly removalPending: boolean;
}

export interface AccountDraft {
  readonly name: string;
  readonly environment: Environment;
  readonly readOnly: boolean;
}

export interface VerifiedAccount {
  readonly account: Account;
  /** Gandi user name behind the token: untrusted data, shown as text only. */
  readonly username: string;
}

export interface AccountChanges {
  readonly newName?: string;
  readonly readOnly?: boolean;
  readonly makeDefault?: boolean;
}

/**
 * A change waiting for the user's confirmation, asked by the server outside the App
 * (dialog of the client or local page); call again with its identifier afterwards.
 */
export interface PendingConfirmation {
  readonly confirmationId: string;
}

export function isPending(value: unknown): value is PendingConfirmation {
  return typeof value === "object" && value !== null && "confirmationId" in value;
}

/** An operation refused by the server; its message is already explained for the user. */
export class AccountsError extends Error {
  override readonly name = "AccountsError";
}

export const NAME_PATTERN = /^[\p{L}\p{N}](?:[\p{L}\p{N}-]| (?! ))*$/u;
export const NAME_MAX_LENGTH = 40;
export const TOKEN_PATTERN = /^[\x21-\x7e]{16,512}$/;

export function isValidName(name: string): boolean {
  const trimmed = name.trim();
  return trimmed.length > 0 && trimmed.length <= NAME_MAX_LENGTH && NAME_PATTERN.test(trimmed);
}

export function isValidToken(token: string): boolean {
  return TOKEN_PATTERN.test(token);
}
