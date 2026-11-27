// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import {
  CONTACT_FIELDS,
  CONTACT_ROLES,
  DomainsError,
  TRANSFER_LOCK_STATUS,
  type ContactCard,
  type ContactDraft,
  type DomainDetails,
  type DomainPage,
  type DomainSummary,
  type PriceBand,
  type Procedure,
  type Quote,
} from "../domain";
import type { DomainsApi } from "../domains-api";
import type { PendingConfirmation } from "../pending-confirmation";
import { callTool, pendingOf, type ToolCaller } from "./tool-caller";

type Wire = Record<string, unknown>;

function record(value: unknown): Wire {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Wire)
    : {};
}

/** A text of Gandi; a withheld long text or any other value gives null. */
function text(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}

function texts(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

function count(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

/** `autorenew` is a flag in a list and an object in the details. */
function autorenew(value: unknown): boolean | null {
  if (typeof value === "boolean") return value;
  const enabled = record(value).enabled;
  return typeof enabled === "boolean" ? enabled : null;
}

function summary(wire: Wire): DomainSummary {
  const fqdn = text(wire.fqdn) ?? "";
  const statuses = texts(wire.status);
  return {
    fqdn,
    displayName: text(wire.fqdn_unicode) ?? fqdn,
    expiresAt: text(record(wire.dates).registry_ends_at),
    autorenew: autorenew(wire.autorenew),
    transferLock: statuses.includes(TRANSFER_LOCK_STATUS),
    statuses,
  };
}

function contacts(value: unknown): ContactCard[] {
  const byRole = record(value);
  return CONTACT_ROLES.flatMap((role) => {
    const contact = record(byRole[role]);
    const fields = CONTACT_FIELDS.flatMap((field) => {
      const shown = text(contact[field]);
      return shown ? [{ field, value: shown }] : [];
    });
    return fields.length > 0 ? [{ role, fields }] : [];
  });
}

function bands(product: Wire): PriceBand[] {
  const prices = Array.isArray(product.prices) ? product.prices : [];
  return prices.flatMap((item) => {
    const band = record(item);
    const unit = band.duration_unit ?? "y";
    const minYears = count(band.min_duration);
    const maxYears = count(band.max_duration);
    const raw = band.price_after_taxes;
    const price =
      typeof raw === "number"
        ? raw
        : typeof raw === "string" && raw.trim() !== ""
          ? Number(raw)
          : NaN;
    return unit === "y" && minYears !== null && maxYears !== null && Number.isFinite(price)
      ? [{ minYears, maxYears, perYearAfterTaxes: price }]
      : [];
  });
}

/** A registration contact as the `domain_register` tool expects it. */
function contactParameter(owner: ContactDraft): Wire {
  return {
    type: owner.type,
    given: owner.given.trim(),
    family: owner.family.trim(),
    email: owner.email.trim(),
    streetaddr: owner.streetaddr.trim(),
    city: owner.city.trim(),
    zip: owner.zip.trim(),
    country: owner.country.trim().toUpperCase(),
    ...(owner.phone.trim() !== "" && { phone: owner.phone.trim() }),
    ...(owner.orgname.trim() !== "" && { orgname: owner.orgname.trim() }),
  };
}

function confirmation(confirmationId: string | undefined): Wire {
  return confirmationId !== undefined ? { confirmation_id: confirmationId } : {};
}

/**
 * Calls the domain tools of the gandi-mcp server, the same ones as the model
 * (ADR 12). Their rules, confirmations and errors apply unchanged; a result of a
 * call made by the App never reaches the model, so contacts are read in full.
 */
export class McpDomainsApi implements DomainsApi {
  constructor(private readonly caller: ToolCaller) {}

  async list(account: string, page: number, perPage: number, filter?: string): Promise<DomainPage> {
    const result = await this.call("domain_list", {
      account,
      page,
      per_page: perPage,
      ...(filter !== undefined && filter.trim() !== "" && { fqdn: filter.trim() }),
    });
    const items = Array.isArray(result.untrusted_data) ? result.untrusted_data : [];
    return {
      domains: items.map((item) => summary(record(item))),
      page: count(result.page) ?? page,
      perPage: count(result.per_page) ?? perPage,
      total: count(result.matching_count) ?? count(result.total_count),
    };
  }

  async details(account: string, fqdn: string): Promise<DomainDetails> {
    const result = await this.call("domain_details", {
      account,
      domain: fqdn,
      include_contact_details: true,
    });
    const wire = record(result.untrusted_data);
    return {
      ...summary(wire),
      createdAt: text(record(wire.dates).created_at),
      nameservers: texts(wire.nameservers),
      tags: texts(wire.tags),
      contacts: contacts(wire.contacts),
    };
  }

  async quote(account: string, fqdn: string, procedure: Procedure): Promise<Quote> {
    const result = await this.call("domain_check_availability", {
      account,
      name: fqdn,
      processes: [procedure],
    });
    const data = record(result.untrusted_data);
    const products = (Array.isArray(data.products) ? data.products : []).map(record);
    const product =
      products.find((item) => item.process === procedure) ??
      (products.length === 1 ? products[0] : undefined) ??
      {};
    return {
      status: procedure === "create" ? text(product.status) : null,
      currency: text(data.currency),
      bands: bands(product),
    };
  }

  async setAutorenew(
    account: string,
    fqdn: string,
    enabled: boolean,
  ): Promise<PendingConfirmation | null> {
    return this.change("domain_autorenew_update", { account, domain: fqdn, enabled });
  }

  async setTransferLock(
    account: string,
    fqdn: string,
    locked: boolean,
    confirmationId?: string,
  ): Promise<PendingConfirmation | null> {
    return locked
      ? this.change("domain_transfer_lock", { account, domain: fqdn })
      : this.change("domain_transfer_unlock", {
          account,
          domain: fqdn,
          ...confirmation(confirmationId),
        });
  }

  async setNameservers(
    account: string,
    fqdn: string,
    nameservers: readonly string[],
    confirmationId?: string,
  ): Promise<PendingConfirmation | null> {
    return this.change("domain_nameservers_update", {
      account,
      domain: fqdn,
      nameservers: [...nameservers],
      ...confirmation(confirmationId),
    });
  }

  async renew(
    account: string,
    fqdn: string,
    years: number,
    confirmationId?: string,
  ): Promise<PendingConfirmation | null> {
    return this.change("domain_renew", {
      account,
      domain: fqdn,
      duration: years,
      ...confirmation(confirmationId),
    });
  }

  async register(
    account: string,
    fqdn: string,
    years: number,
    owner: ContactDraft,
    confirmationId?: string,
  ): Promise<PendingConfirmation | null> {
    return this.change("domain_register", {
      account,
      domain: fqdn,
      duration: years,
      owner: contactParameter(owner),
      ...confirmation(confirmationId),
    });
  }

  private async change(name: string, args: Wire): Promise<PendingConfirmation | null> {
    return pendingOf(await this.call(name, args));
  }

  private call(name: string, args: Wire): Promise<Wire> {
    return callTool(this.caller, name, args, (message) => new DomainsError(message));
  }
}
