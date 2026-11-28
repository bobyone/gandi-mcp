// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import type { CreationOutcome, RecordDraft, RecordPage, Snapshot } from "./livedns";
import type { PendingConfirmation } from "./pending-confirmation";

/**
 * LiveDNS operations offered to the MCP App. Every operation rejects with a
 * `LiveDnsError` carrying a message for the user. Destructive changes may come back
 * pending (null means done): the server asks the user outside the App, then the App
 * calls again with the confirmation identifier.
 */
export interface LiveDnsApi {
  /** The LiveDNS domains of the account (ASCII names). */
  domains(account: string): Promise<string[]>;
  /** The record types LiveDNS supports. */
  recordTypes(account: string): Promise<string[]>;
  /** A page of records with their full values; `type` filters them. */
  records(
    account: string,
    zone: string,
    page: number,
    perPage: number,
    type?: string,
  ): Promise<RecordPage>;
  createRecord(account: string, zone: string, record: RecordDraft): Promise<CreationOutcome>;
  /** Replace the values and TTL of the record of this name and type. */
  replaceRecord(
    account: string,
    zone: string,
    record: RecordDraft,
    confirmationId?: string,
  ): Promise<PendingConfirmation | null>;
  deleteRecord(
    account: string,
    zone: string,
    name: string,
    type: string,
    confirmationId?: string,
  ): Promise<PendingConfirmation | null>;
  /** The latest snapshots of the zone, newest first. */
  snapshots(account: string, zone: string): Promise<Snapshot[]>;
  createSnapshot(account: string, zone: string, name?: string): Promise<void>;
  /** Replace every record of the zone with those of the snapshot. */
  restoreSnapshot(
    account: string,
    zone: string,
    snapshotId: string,
    confirmationId?: string,
  ): Promise<PendingConfirmation | null>;
}
