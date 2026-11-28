// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import { describe, expect, it, vi } from "vitest";
import { LiveDnsError } from "../../../src/api/livedns";
import { McpLiveDnsApi } from "../../../src/api/mcp/mcp-livedns-api";
import type { ToolCaller } from "../../../src/api/mcp/tool-caller";

type Result = Awaited<ReturnType<ToolCaller["callServerTool"]>>;

function caller(...results: Result[]) {
  const fake = vi.fn<ToolCaller["callServerTool"]>();
  for (const result of results) fake.mockResolvedValueOnce(result);
  return { callServerTool: fake };
}

function framed(data: unknown, extra: Record<string, unknown> = {}): Result {
  return { structuredContent: { notice: "untrusted", untrusted_data: data, ...extra } };
}

function calls(fake: ReturnType<typeof caller>) {
  return fake.callServerTool.mock.calls.map((call) => call[0] as unknown);
}

const PENDING: Result = {
  structuredContent: { status: "confirmation_pending", confirmation_id: "c-1" },
};
const DONE: Result = framed({}, { status: "done" });
const DKIM = `"v=DKIM1; p=${"A".repeat(400)}"`;

describe("McpLiveDnsApi", () => {
  it("lists the LiveDNS domains and the record types", async () => {
    const fake = caller(
      framed([{ fqdn: "example.com" }, { fqdn: 3 }, "odd"]),
      framed(["A", "TXT", 5]),
    );
    const api = new McpLiveDnsApi(fake);

    expect(await api.domains("Perso")).toEqual(["example.com"]);
    expect(await api.recordTypes("Perso")).toEqual(["A", "TXT"]);
    expect(calls(fake)).toEqual([
      { name: "livedns_domains", arguments: { account: "Perso", page: 1, per_page: 100 } },
      { name: "livedns_record_types", arguments: { account: "Perso" } },
    ]);
  });

  it("reads a page of records in full through the app-only tool", async () => {
    const fake = caller(
      framed(
        [
          {
            rrset_name: "default._domainkey",
            rrset_type: "TXT",
            rrset_ttl: 300,
            rrset_values: [DKIM, 7],
          },
          { rrset_name: "www", rrset_type: "A", rrset_values: "odd" },
          { rrset_type: "A" },
        ],
        { page: 2, per_page: 25, total_count: 30 },
      ),
      framed([]),
    );
    const api = new McpLiveDnsApi(fake);

    const page = await api.records("Perso", "example.com", 2, 25, "TXT");
    const empty = await api.records("Perso", "example.com", 1, 25, "");

    expect(page).toEqual({
      records: [
        { name: "default._domainkey", type: "TXT", ttl: 300, values: [DKIM] },
        { name: "www", type: "A", ttl: null, values: [] },
      ],
      page: 2,
      perPage: 25,
      total: 30,
    });
    expect(empty).toEqual({ records: [], page: 1, perPage: 25, total: null });
    expect(calls(fake)).toEqual([
      {
        name: "app_livedns_records",
        arguments: {
          account: "Perso",
          domain: "example.com",
          page: 2,
          per_page: 25,
          record_type: "TXT",
        },
      },
      {
        name: "app_livedns_records",
        arguments: { account: "Perso", domain: "example.com", page: 1, per_page: 25 },
      },
    ]);
  });

  it("creates a record and tells an identical one apart", async () => {
    const fake = caller(DONE, framed({}, { status: "unchanged" }));
    const api = new McpLiveDnsApi(fake);
    const draft = { name: " www ", type: "A", ttl: 600, values: ["192.0.2.1"] };

    expect(await api.createRecord("Perso", "example.com", draft)).toBe("created");
    expect(await api.createRecord("Perso", "example.com", { ...draft, ttl: null })).toBe(
      "unchanged",
    );
    expect(calls(fake)).toEqual([
      {
        name: "livedns_record_create",
        arguments: {
          account: "Perso",
          domain: "example.com",
          name: "www",
          record_type: "A",
          values: ["192.0.2.1"],
          ttl: 600,
        },
      },
      {
        name: "livedns_record_create",
        arguments: {
          account: "Perso",
          domain: "example.com",
          name: "www",
          record_type: "A",
          values: ["192.0.2.1"],
        },
      },
    ]);
  });

  it("replaces and deletes a record, resuming with the confirmation", async () => {
    const fake = caller(PENDING, DONE, PENDING, DONE);
    const api = new McpLiveDnsApi(fake);
    const draft = { name: "www", type: "A", ttl: null, values: ["192.0.2.2"] };

    expect(await api.replaceRecord("Perso", "example.com", draft)).toEqual({
      confirmationId: "c-1",
    });
    expect(await api.replaceRecord("Perso", "example.com", draft, "c-1")).toBeNull();
    expect(await api.deleteRecord("Perso", "example.com", "www", "A")).toEqual({
      confirmationId: "c-1",
    });
    expect(await api.deleteRecord("Perso", "example.com", "www", "A", "c-1")).toBeNull();
    expect(calls(fake)).toEqual([
      {
        name: "livedns_record_replace",
        arguments: {
          account: "Perso",
          domain: "example.com",
          name: "www",
          record_type: "A",
          values: ["192.0.2.2"],
        },
      },
      {
        name: "livedns_record_replace",
        arguments: {
          account: "Perso",
          domain: "example.com",
          name: "www",
          record_type: "A",
          values: ["192.0.2.2"],
          confirmation_id: "c-1",
        },
      },
      {
        name: "livedns_record_delete",
        arguments: { account: "Perso", domain: "example.com", name: "www", record_type: "A" },
      },
      {
        name: "livedns_record_delete",
        arguments: {
          account: "Perso",
          domain: "example.com",
          name: "www",
          record_type: "A",
          confirmation_id: "c-1",
        },
      },
    ]);
  });

  it("lists, creates and restores snapshots", async () => {
    const fake = caller(
      framed([
        {
          id: "snap-1",
          name: "before",
          automatic: false,
          created_at: "2026-11-28T06:49:28Z",
        },
        { id: "snap-2", automatic: "odd" },
        { name: "no id" },
      ]),
      DONE,
      DONE,
      PENDING,
      DONE,
    );
    const api = new McpLiveDnsApi(fake);

    expect(await api.snapshots("Perso", "example.com")).toEqual([
      { id: "snap-1", name: "before", automatic: false, createdAt: "2026-11-28T06:49:28Z" },
      { id: "snap-2", name: "snap-2", automatic: null, createdAt: null },
    ]);
    await api.createSnapshot("Perso", "example.com", " test ");
    await api.createSnapshot("Perso", "example.com", " ");
    expect(await api.restoreSnapshot("Perso", "example.com", "snap-1")).toEqual({
      confirmationId: "c-1",
    });
    expect(await api.restoreSnapshot("Perso", "example.com", "snap-1", "c-1")).toBeNull();
    expect(calls(fake)).toEqual([
      {
        name: "livedns_snapshots",
        arguments: {
          account: "Perso",
          domain: "example.com",
          sort_by: "-date_created",
          page: 1,
          per_page: 25,
        },
      },
      {
        name: "livedns_snapshot_create",
        arguments: { account: "Perso", domain: "example.com", name: "test" },
      },
      { name: "livedns_snapshot_create", arguments: { account: "Perso", domain: "example.com" } },
      {
        name: "livedns_snapshot_restore",
        arguments: { account: "Perso", domain: "example.com", snapshot_id: "snap-1" },
      },
      {
        name: "livedns_snapshot_restore",
        arguments: {
          account: "Perso",
          domain: "example.com",
          snapshot_id: "snap-1",
          confirmation_id: "c-1",
        },
      },
    ]);
  });

  it("turns a refusal into a LiveDNS error with the server explanation", async () => {
    const fake = caller({
      isError: true,
      content: [{ type: "text", text: "This account is read-only." }],
    });

    const failure = new McpLiveDnsApi(fake).domains("Watch");

    await expect(failure).rejects.toThrow(LiveDnsError);
    await expect(failure).rejects.toThrow("This account is read-only.");
  });
});
