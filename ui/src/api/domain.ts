// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
/**
 * Values exchanged with the server about domains. Everything read from Gandi is
 * untrusted data: it is shown as text only, never as HTML.
 */

/** Gandi status code meaning the transfer lock is set. */
export const TRANSFER_LOCK_STATUS = "clientTransferProhibited";

export interface DomainSummary {
  /** ASCII name, used to call the tools. */
  readonly fqdn: string;
  /** Name to display (Unicode for an internationalized name). */
  readonly displayName: string;
  /** Expiry date at the registry, ISO 8601 in UTC. */
  readonly expiresAt: string | null;
  readonly autorenew: boolean | null;
  readonly transferLock: boolean;
  readonly statuses: readonly string[];
}

export interface DomainPage {
  readonly domains: readonly DomainSummary[];
  readonly page: number;
  readonly perPage: number;
  /** Number of domains matching the filter, when Gandi gives it. */
  readonly total: number | null;
}

export type ContactRole = "owner" | "admin" | "tech" | "bill";
export const CONTACT_ROLES: readonly ContactRole[] = ["owner", "admin", "tech", "bill"];

/** Contact fields shown and typed in the App, in display order. */
export const CONTACT_FIELDS = [
  "orgname",
  "given",
  "family",
  "email",
  "phone",
  "streetaddr",
  "zip",
  "city",
  "country",
] as const;
export type ContactField = (typeof CONTACT_FIELDS)[number];

/** A domain contact as Gandi returns it, in full: the App sends nothing to the model. */
export interface ContactCard {
  readonly role: ContactRole;
  /** The fields Gandi gave, in display order. */
  readonly fields: readonly { readonly field: ContactField; readonly value: string }[];
}

export interface DomainDetails extends DomainSummary {
  readonly createdAt: string | null;
  readonly nameservers: readonly string[];
  readonly tags: readonly string[];
  readonly contacts: readonly ContactCard[];
}

/** A price band of a quote: a price per year for durations from `minYears` to `maxYears`. */
export interface PriceBand {
  readonly minYears: number;
  readonly maxYears: number;
  readonly perYearAfterTaxes: number;
}

/** What Gandi announces for one procedure on a name; indicative until the confirmation. */
export interface Quote {
  /** Availability status for a registration (`available`...), else null. */
  readonly status: string | null;
  readonly currency: string | null;
  readonly bands: readonly PriceBand[];
}

export type Procedure = "create" | "renew";

export const CONTACT_TYPES = ["individual", "company", "association", "publicbody"] as const;
export type ContactType = (typeof CONTACT_TYPES)[number];

/** The owner typed by the user for a registration. */
export interface ContactDraft {
  readonly type: ContactType;
  readonly given: string;
  readonly family: string;
  readonly orgname: string;
  readonly email: string;
  readonly phone: string;
  readonly streetaddr: string;
  readonly city: string;
  readonly zip: string;
  readonly country: string;
}

/** An operation refused by the server; its message is already explained for the user. */
export class DomainsError extends Error {
  override readonly name = "DomainsError";
}

export const MIN_YEARS = 1;
export const MAX_YEARS = 10;
export const MAX_NAMESERVERS = 13;
export const COUNTRY_PATTERN = /^[A-Za-z]{2}$/;
export const PHONE_PATTERN = /^\+\d{1,3}\.\d{4,14}$/;

/** The band whose durations include `years`, if exactly one price applies. */
export function bandFor(quote: Quote, years: number): PriceBand | null {
  const matching = quote.bands.filter((band) => band.minYears <= years && years <= band.maxYears);
  const prices = new Set(matching.map((band) => band.perYearAfterTaxes));
  return prices.size === 1 ? (matching[0] ?? null) : null;
}

/** Durations offered by a quote, within the bounds accepted by the server. */
export function durations(quote: Quote): number[] {
  const years = new Set<number>();
  for (const band of quote.bands) {
    for (let y = Math.max(band.minYears, MIN_YEARS); y <= Math.min(band.maxYears, MAX_YEARS); y++)
      years.add(y);
  }
  return [...years].sort((a, b) => a - b);
}

/** Split typed nameservers, one per line; null when there are none or too many. */
export function parseNameservers(text: string): string[] | null {
  const names = text
    .split(/\s+/)
    .map((name) => name.trim())
    .filter((name) => name !== "");
  return names.length >= 1 && names.length <= MAX_NAMESERVERS ? names : null;
}

export const EMPTY_CONTACT: ContactDraft = {
  type: "individual",
  given: "",
  family: "",
  orgname: "",
  email: "",
  phone: "",
  streetaddr: "",
  city: "",
  zip: "",
  country: "",
};

/** Fields of a contact draft that are missing or badly formed; the server checks again. */
export function invalidContactFields(contact: ContactDraft): Set<ContactField> {
  const invalid = new Set<ContactField>();
  const required: ContactField[] = ["given", "family", "streetaddr", "city", "zip"];
  for (const field of required) if (contact[field].trim() === "") invalid.add(field);
  if (!/^[^\s@]+@[^\s@]+$/.test(contact.email.trim())) invalid.add("email");
  if (!COUNTRY_PATTERN.test(contact.country.trim())) invalid.add("country");
  if (contact.phone.trim() !== "" && !PHONE_PATTERN.test(contact.phone.trim()))
    invalid.add("phone");
  if (contact.type !== "individual" && contact.orgname.trim() === "") invalid.add("orgname");
  return invalid;
}

/** Whether a typed name looks like a domain name; the server checks it fully. */
export function looksLikeDomain(name: string): boolean {
  const trimmed = name.trim();
  return trimmed.length <= 253 && /^[^\s./][^\s/]*\.[^\s./]+$/u.test(trimmed);
}

/** Availability statuses of Gandi under which a name can be registered. */
const AVAILABLE = new Set(["available", "available_reserved", "available_preorder"]);

export function isAvailable(quote: Quote): boolean {
  return quote.status !== null && AVAILABLE.has(quote.status);
}

/** The chosen duration if the quote offers it, else its shortest one. */
export function pickYears(quote: Quote, years: number): number {
  const offered = durations(quote);
  return offered.length === 0 || offered.includes(years) ? years : (offered[0] ?? years);
}
