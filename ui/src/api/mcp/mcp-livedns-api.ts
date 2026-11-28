// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import {
  LiveDnsError,
  type CreationOutcome,
  type DnsRecord,
  type RecordDraft,
  type RecordPage,
  type Snapshot,
} from "../livedns";
import type { LiveDnsApi } from "../livedns-api";
import type { PendingConfirmation } from "../pending-confirmation";
import { callTool, pendingOf, type ToolCaller } from "./tool-caller";

type Wire = Record<string, unknown>;

/** Domains read at once: the screen offers a list, not a search. */
const DOMAINS_PER_PAGE = 100;
const SNAPSHOTS_PER_PAGE = 25;

function record(value: unknown): Wire {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Wire)
    : {};
}

function items(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

/** A text of Gandi; a withheld text or any other value gives null. */
function text(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}

function texts(value: unknown): string[] {
  return items(value).filter((item): item is string => typeof item === "string");
}

function count(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function dnsRecord(wire: Wire): DnsRecord | null {
  const name = text(wire.rrset_name);
  const type = text(wire.rrset_type);
  return name !== null && type !== null
    ? { name, type, ttl: count(wire.rrset_ttl), values: texts(wire.rrset_values) }
    : null;
}

function snapshot(wire: Wire): Snapshot | null {
  const id = text(wire.id);
  return id !== null
    ? {
        id,
        name: text(wire.name) ?? id,
        automatic: typeof wire.automatic === "boolean" ? wire.automatic : null,
        createdAt: text(wire.created_at),
      }
    : null;
}

function confirmation(confirmationId: string | undefined): Wire {
  return confirmationId !== undefined ? { confirmation_id: confirmationId } : {};
}

/** A record as the write tools expect it. */
function recordArguments(draft: RecordDraft): Wire {
  return {
    name: draft.name.trim(),
    record_type: draft.type,
    values: [...draft.values],
    ...(draft.ttl !== null && { ttl: draft.ttl }),
  };
}

/**
 * Calls the LiveDNS tools of the gandi-mcp server: the app-only
 * `app_livedns_records`, which returns full values, and the model tools for
 * everything else (ADR 12, ADR 16). A result of a call made by the App never
 * reaches the model.
 */
export class McpLiveDnsApi implements LiveDnsApi {
  constructor(private readonly caller: ToolCaller) {}

  async domains(account: string): Promise<string[]> {
    const result = await this.call("livedns_domains", {
      account,
      page: 1,
      per_page: DOMAINS_PER_PAGE,
    });
    return items(result.untrusted_data).flatMap((item) => {
      const fqdn = text(record(item).fqdn);
      return fqdn !== null ? [fqdn] : [];
    });
  }

  async recordTypes(account: string): Promise<string[]> {
    const result = await this.call("livedns_record_types", { account });
    return texts(result.untrusted_data);
  }

  async records(
    account: string,
    zone: string,
    page: number,
    perPage: number,
    type?: string,
  ): Promise<RecordPage> {
    const result = await this.call("app_livedns_records", {
      account,
      domain: zone,
      page,
      per_page: perPage,
      ...(type !== undefined && type !== "" && { record_type: type }),
    });
    return {
      records: items(result.untrusted_data).flatMap((item) => {
        const found = dnsRecord(record(item));
        return found !== null ? [found] : [];
      }),
      page: count(result.page) ?? page,
      perPage: count(result.per_page) ?? perPage,
      total: count(result.total_count),
    };
  }

  async createRecord(account: string, zone: string, draft: RecordDraft): Promise<CreationOutcome> {
    const result = await this.call("livedns_record_create", {
      account,
      domain: zone,
      ...recordArguments(draft),
    });
    return result.status === "unchanged" ? "unchanged" : "created";
  }

  async replaceRecord(
    account: string,
    zone: string,
    draft: RecordDraft,
    confirmationId?: string,
  ): Promise<PendingConfirmation | null> {
    return this.change("livedns_record_replace", {
      account,
      domain: zone,
      ...recordArguments(draft),
      ...confirmation(confirmationId),
    });
  }

  async deleteRecord(
    account: string,
    zone: string,
    name: string,
    type: string,
    confirmationId?: string,
  ): Promise<PendingConfirmation | null> {
    return this.change("livedns_record_delete", {
      account,
      domain: zone,
      name,
      record_type: type,
      ...confirmation(confirmationId),
    });
  }

  async snapshots(account: string, zone: string): Promise<Snapshot[]> {
    const result = await this.call("livedns_snapshots", {
      account,
      domain: zone,
      sort_by: "-date_created",
      page: 1,
      per_page: SNAPSHOTS_PER_PAGE,
    });
    return items(result.untrusted_data).flatMap((item) => {
      const found = snapshot(record(item));
      return found !== null ? [found] : [];
    });
  }

  async createSnapshot(account: string, zone: string, name?: string): Promise<void> {
    const trimmed = name?.trim() ?? "";
    await this.call("livedns_snapshot_create", {
      account,
      domain: zone,
      ...(trimmed !== "" && { name: trimmed }),
    });
  }

  async restoreSnapshot(
    account: string,
    zone: string,
    snapshotId: string,
    confirmationId?: string,
  ): Promise<PendingConfirmation | null> {
    return this.change("livedns_snapshot_restore", {
      account,
      domain: zone,
      snapshot_id: snapshotId,
      ...confirmation(confirmationId),
    });
  }

  private async change(name: string, args: Wire): Promise<PendingConfirmation | null> {
    return pendingOf(await this.call(name, args));
  }

  private call(name: string, args: Wire): Promise<Wire> {
    return callTool(this.caller, name, args, (message) => new LiveDnsError(message));
  }
}
