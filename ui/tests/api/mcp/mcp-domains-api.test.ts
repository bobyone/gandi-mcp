// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import { describe, expect, it, vi } from "vitest";
import { DomainsError, EMPTY_CONTACT } from "../../../src/api/domain";
import { McpDomainsApi } from "../../../src/api/mcp/mcp-domains-api";
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

describe("McpDomainsApi", () => {
  it("lists a page of domains with its filter", async () => {
    const fake = caller(
      framed(
        [
          {
            fqdn: "xn--caf-dma.fr",
            fqdn_unicode: "café.fr",
            dates: { registry_ends_at: "2027-03-01T00:00:00Z" },
            autorenew: true,
            status: ["clientTransferProhibited"],
          },
          { fqdn: "example.com", autorenew: { enabled: false }, status: "odd", dates: 3 },
          "not a domain",
        ],
        { page: 2, per_page: 25, total_count: 40, matching_count: 27 },
      ),
    );

    const page = await new McpDomainsApi(fake).list("Perso", 2, 25, " *.fr ");

    expect(page).toEqual({
      domains: [
        {
          fqdn: "xn--caf-dma.fr",
          displayName: "café.fr",
          expiresAt: "2027-03-01T00:00:00Z",
          autorenew: true,
          transferLock: true,
          statuses: ["clientTransferProhibited"],
        },
        {
          fqdn: "example.com",
          displayName: "example.com",
          expiresAt: null,
          autorenew: false,
          transferLock: false,
          statuses: [],
        },
        {
          fqdn: "",
          displayName: "",
          expiresAt: null,
          autorenew: null,
          transferLock: false,
          statuses: [],
        },
      ],
      page: 2,
      perPage: 25,
      total: 27,
    });
    expect(calls(fake)).toEqual([
      {
        name: "domain_list",
        arguments: { account: "Perso", page: 2, per_page: 25, fqdn: "*.fr" },
      },
    ]);
  });

  it("lists without a filter and without counts", async () => {
    const fake = caller(framed({ withheld: "long_text" }), framed([], { total_count: 3 }));
    const api = new McpDomainsApi(fake);

    await expect(api.list("Perso", 1, 25, "  ")).resolves.toEqual({
      domains: [],
      page: 1,
      perPage: 25,
      total: null,
    });
    await expect(api.list("Perso", 1, 25)).resolves.toMatchObject({ total: 3 });
    expect(calls(fake)).toEqual([
      { name: "domain_list", arguments: { account: "Perso", page: 1, per_page: 25 } },
      { name: "domain_list", arguments: { account: "Perso", page: 1, per_page: 25 } },
    ]);
  });

  it("describes a domain with its contacts in full", async () => {
    const fake = caller(
      framed({
        fqdn: "example.com",
        dates: { created_at: "2020-01-01T00:00:00Z", registry_ends_at: "2027-01-01T00:00:00Z" },
        autorenew: { enabled: true, duration: 1 },
        status: [],
        nameservers: ["ns1.gandi.net", 7],
        tags: ["perso"],
        contacts: {
          owner: { given: "Ada", family: "Lovelace", email: "ada@example.com", country: "FR" },
          admin: { orgname: { withheld: "long_text", length: 400 } },
          tech: "hidden",
        },
      }),
    );

    const details = await new McpDomainsApi(fake).details("Perso", "example.com");

    expect(details).toMatchObject({
      fqdn: "example.com",
      createdAt: "2020-01-01T00:00:00Z",
      autorenew: true,
      nameservers: ["ns1.gandi.net"],
      tags: ["perso"],
      contacts: [
        {
          role: "owner",
          fields: [
            { field: "given", value: "Ada" },
            { field: "family", value: "Lovelace" },
            { field: "email", value: "ada@example.com" },
            { field: "country", value: "FR" },
          ],
        },
      ],
    });
    expect(calls(fake)).toEqual([
      {
        name: "domain_details",
        arguments: { account: "Perso", domain: "example.com", include_contact_details: true },
      },
    ]);
  });

  it("reads the price bands of a procedure", async () => {
    const fake = caller(
      framed({
        currency: "EUR",
        products: [
          {
            process: "create",
            status: "available",
            prices: [
              { min_duration: 1, max_duration: 1, duration_unit: "y", price_after_taxes: "12.00" },
              { min_duration: 2, max_duration: 10, price_after_taxes: 10 },
              { min_duration: 1, max_duration: 12, duration_unit: "m", price_after_taxes: 1 },
              { min_duration: "1", max_duration: 2, price_after_taxes: 1 },
              { min_duration: 1, max_duration: 2, price_after_taxes: "free" },
              { min_duration: 1, max_duration: 2, price_after_taxes: null },
              "odd",
            ],
          },
        ],
      }),
    );

    await expect(new McpDomainsApi(fake).quote("Perso", "example.com", "create")).resolves.toEqual({
      status: "available",
      currency: "EUR",
      bands: [
        { minYears: 1, maxYears: 1, perYearAfterTaxes: 12 },
        { minYears: 2, maxYears: 10, perYearAfterTaxes: 10 },
      ],
    });
    expect(calls(fake)).toEqual([
      {
        name: "domain_check_availability",
        arguments: { account: "Perso", name: "example.com", processes: ["create"] },
      },
    ]);
  });

  it("reads a renewal price without availability, or nothing", async () => {
    const fake = caller(
      framed({ products: [{ status: "unavailable", prices: [] }] }),
      framed({ currency: "EUR", products: [{ process: "create" }, { process: "transfer" }] }),
      framed("odd"),
    );
    const api = new McpDomainsApi(fake);

    await expect(api.quote("Perso", "example.com", "renew")).resolves.toEqual({
      status: null,
      currency: null,
      bands: [],
    });
    await expect(api.quote("Perso", "example.com", "renew")).resolves.toEqual({
      status: null,
      currency: "EUR",
      bands: [],
    });
    await expect(api.quote("Perso", "example.com", "renew")).resolves.toEqual({
      status: null,
      currency: null,
      bands: [],
    });
  });

  it("changes the settings and resumes the confirmed ones", async () => {
    const fake = caller(DONE, DONE, PENDING, DONE, PENDING, DONE);
    const api = new McpDomainsApi(fake);

    await expect(api.setAutorenew("Perso", "example.com", false)).resolves.toBeNull();
    await expect(api.setTransferLock("Perso", "example.com", true)).resolves.toBeNull();
    await expect(api.setTransferLock("Perso", "example.com", false)).resolves.toEqual({
      confirmationId: "c-1",
    });
    await api.setTransferLock("Perso", "example.com", false, "c-1");
    await expect(api.setNameservers("Perso", "example.com", ["ns1.example.net"])).resolves.toEqual({
      confirmationId: "c-1",
    });
    await api.setNameservers("Perso", "example.com", ["ns1.example.net"], "c-1");

    expect(calls(fake)).toEqual([
      {
        name: "domain_autorenew_update",
        arguments: { account: "Perso", domain: "example.com", enabled: false },
      },
      { name: "domain_transfer_lock", arguments: { account: "Perso", domain: "example.com" } },
      { name: "domain_transfer_unlock", arguments: { account: "Perso", domain: "example.com" } },
      {
        name: "domain_transfer_unlock",
        arguments: { account: "Perso", domain: "example.com", confirmation_id: "c-1" },
      },
      {
        name: "domain_nameservers_update",
        arguments: { account: "Perso", domain: "example.com", nameservers: ["ns1.example.net"] },
      },
      {
        name: "domain_nameservers_update",
        arguments: {
          account: "Perso",
          domain: "example.com",
          nameservers: ["ns1.example.net"],
          confirmation_id: "c-1",
        },
      },
    ]);
  });

  it("orders a renewal and a registration with the owner for every role", async () => {
    const fake = caller(PENDING, DONE, PENDING, DONE);
    const api = new McpDomainsApi(fake);
    const owner = {
      ...EMPTY_CONTACT,
      given: " Ada ",
      family: "Lovelace",
      email: "ada@example.com",
      streetaddr: "1 rue de la Paix",
      city: "Paris",
      zip: "75002",
      country: "fr",
    };

    await expect(api.renew("Perso", "example.com", 2)).resolves.toEqual({ confirmationId: "c-1" });
    await api.renew("Perso", "example.com", 2, "c-1");
    await api.register("Perso", "new.fr", 1, owner);
    await api.register(
      "Perso",
      "new.fr",
      1,
      { ...owner, type: "company", orgname: "Ada SARL", phone: "+33.123456789" },
      "c-1",
    );

    const sent = {
      type: "individual",
      given: "Ada",
      family: "Lovelace",
      email: "ada@example.com",
      streetaddr: "1 rue de la Paix",
      city: "Paris",
      zip: "75002",
      country: "FR",
    };
    expect(calls(fake)).toEqual([
      { name: "domain_renew", arguments: { account: "Perso", domain: "example.com", duration: 2 } },
      {
        name: "domain_renew",
        arguments: { account: "Perso", domain: "example.com", duration: 2, confirmation_id: "c-1" },
      },
      {
        name: "domain_register",
        arguments: { account: "Perso", domain: "new.fr", duration: 1, owner: sent },
      },
      {
        name: "domain_register",
        arguments: {
          account: "Perso",
          domain: "new.fr",
          duration: 1,
          owner: { ...sent, type: "company", orgname: "Ada SARL", phone: "+33.123456789" },
          confirmation_id: "c-1",
        },
      },
    ]);
  });

  it("turns refusals and transport failures into domain errors", async () => {
    const refused = caller({
      isError: true,
      content: [{ type: "text", text: "Read-only account" }],
    });
    const failing = { callServerTool: vi.fn().mockRejectedValue(new Error("disconnected")) };

    await expect(new McpDomainsApi(refused).setAutorenew("Perso", "a.fr", true)).rejects.toEqual(
      new DomainsError("Read-only account"),
    );
    await expect(new McpDomainsApi(failing).list("Perso", 1, 25)).rejects.toEqual(
      new DomainsError("disconnected"),
    );
  });
});
