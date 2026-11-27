// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import type { ContactDraft, DomainDetails, DomainPage, Procedure, Quote } from "./domain";
import type { PendingConfirmation } from "./pending-confirmation";

/**
 * Domain operations offered to the MCP App. Every operation rejects with a
 * `DomainsError` carrying a message for the user. Confirmed and billable changes may
 * come back pending (null means done): the server asks the user outside the App, then the App calls
 * again with the confirmation identifier.
 */
export interface DomainsApi {
  list(account: string, page: number, perPage: number, filter?: string): Promise<DomainPage>;
  details(account: string, fqdn: string): Promise<DomainDetails>;
  /** Indicative availability and prices; the exact amount comes with the confirmation. */
  quote(account: string, fqdn: string, procedure: Procedure): Promise<Quote>;
  setAutorenew(
    account: string,
    fqdn: string,
    enabled: boolean,
  ): Promise<PendingConfirmation | null>;
  setTransferLock(
    account: string,
    fqdn: string,
    locked: boolean,
    confirmationId?: string,
  ): Promise<PendingConfirmation | null>;
  setNameservers(
    account: string,
    fqdn: string,
    nameservers: readonly string[],
    confirmationId?: string,
  ): Promise<PendingConfirmation | null>;
  renew(
    account: string,
    fqdn: string,
    years: number,
    confirmationId?: string,
  ): Promise<PendingConfirmation | null>;
  /** Register with the owner used for every contact role. */
  register(
    account: string,
    fqdn: string,
    years: number,
    owner: ContactDraft,
    confirmationId?: string,
  ): Promise<PendingConfirmation | null>;
}
