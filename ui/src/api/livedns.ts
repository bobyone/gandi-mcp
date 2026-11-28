// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
/**
 * Values exchanged with the server about LiveDNS zones. Everything read from Gandi
 * is untrusted data: it is shown as text only, never as HTML.
 */

/** TTL bounds of LiveDNS, in seconds. */
export const MIN_TTL = 300;
export const MAX_TTL = 2_592_000;
/** Values of one record, as the server accepts them. */
export const MAX_VALUES = 100;
export const MAX_VALUE_LENGTH = 16_384;
/** A record name relative to its zone, without spaces; the server checks the rest. */
const RECORD_NAME = /^\S{1,255}$/u;
const PRINTABLE_ASCII = /^[\x20-\x7e]+$/;

/** A record of a zone: the values of one name and one type. */
export interface DnsRecord {
  readonly name: string;
  readonly type: string;
  /** In seconds, when Gandi gives it. */
  readonly ttl: number | null;
  readonly values: readonly string[];
}

export interface RecordPage {
  readonly records: readonly DnsRecord[];
  readonly page: number;
  readonly perPage: number;
  /** Number of records of the zone (or of the type), when Gandi gives it. */
  readonly total: number | null;
}

/** A record as the user types it; the TTL is null for the LiveDNS default. */
export interface RecordDraft {
  readonly name: string;
  readonly type: string;
  readonly ttl: number | null;
  readonly values: readonly string[];
}

export interface Snapshot {
  readonly id: string;
  readonly name: string;
  readonly automatic: boolean | null;
  /** ISO 8601 in UTC. */
  readonly createdAt: string | null;
}

/** What a record creation did: created, or nothing when the same record exists. */
export type CreationOutcome = "created" | "unchanged";

export class LiveDnsError extends Error {
  override readonly name = "LiveDnsError";
}

/** The values typed one per line, or null when one is invalid or there are none. */
export function parseValues(text: string): string[] | null {
  const values = [
    ...new Set(
      text
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter((line) => line !== ""),
    ),
  ];
  if (values.length === 0 || values.length > MAX_VALUES) return null;
  return values.every((value) => value.length <= MAX_VALUE_LENGTH && PRINTABLE_ASCII.test(value))
    ? values
    : null;
}

/** The TTL typed, null when empty, undefined when out of bounds or not a number. */
export function parseTtl(text: string): number | null | undefined {
  const trimmed = text.trim();
  if (trimmed === "") return null;
  if (!/^\d+$/.test(trimmed)) return undefined;
  const seconds = Number(trimmed);
  return seconds >= MIN_TTL && seconds <= MAX_TTL ? seconds : undefined;
}

export function isRecordName(text: string): boolean {
  return RECORD_NAME.test(text.trim());
}
