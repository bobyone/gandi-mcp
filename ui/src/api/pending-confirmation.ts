// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

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
