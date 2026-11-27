// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import { describe, expect, it } from "vitest";
import {
  EMPTY_CONTACT,
  bandFor,
  durations,
  invalidContactFields,
  isAvailable,
  looksLikeDomain,
  parseNameservers,
  pickYears,
  type Quote,
} from "../../src/api/domain";

const QUOTE: Quote = {
  status: "available",
  currency: "EUR",
  bands: [
    { minYears: 1, maxYears: 1, perYearAfterTaxes: 12 },
    { minYears: 2, maxYears: 10, perYearAfterTaxes: 10 },
  ],
};

const OWNER = {
  ...EMPTY_CONTACT,
  given: "Ada",
  family: "Lovelace",
  email: "ada@example.com",
  streetaddr: "1 rue de la Paix",
  city: "Paris",
  zip: "75002",
  country: "FR",
};

describe("domain values", () => {
  it("finds the one band of a duration", () => {
    expect(bandFor(QUOTE, 1)?.perYearAfterTaxes).toBe(12);
    expect(bandFor(QUOTE, 5)?.perYearAfterTaxes).toBe(10);
    expect(bandFor(QUOTE, 11)).toBeNull();
  });

  it("refuses to pick between different prices for the same duration", () => {
    const phases: Quote = {
      ...QUOTE,
      bands: [...QUOTE.bands, { minYears: 1, maxYears: 1, perYearAfterTaxes: 90 }],
    };

    expect(bandFor(phases, 1)).toBeNull();
    expect(
      bandFor({ ...QUOTE, bands: [QUOTE.bands[0]!, QUOTE.bands[0]!] }, 1)?.perYearAfterTaxes,
    ).toBe(12);
  });

  it("offers the durations of the bands within the accepted bounds", () => {
    expect(durations(QUOTE)).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
    expect(
      durations({ ...QUOTE, bands: [{ minYears: 0, maxYears: 99, perYearAfterTaxes: 1 }] }),
    ).toHaveLength(10);
    expect(
      pickYears({ ...QUOTE, bands: [{ minYears: 2, maxYears: 3, perYearAfterTaxes: 1 }] }, 1),
    ).toBe(2);
    expect(pickYears(QUOTE, 4)).toBe(4);
    expect(pickYears({ ...QUOTE, bands: [] }, 4)).toBe(4);
  });

  it("tells whether a name can be registered", () => {
    expect(isAvailable(QUOTE)).toBe(true);
    expect(isAvailable({ ...QUOTE, status: "unavailable" })).toBe(false);
    expect(isAvailable({ ...QUOTE, status: null })).toBe(false);
  });

  it("splits the nameservers typed one per line", () => {
    expect(parseNameservers(" ns1.example.net\n\nns2.example.net ")).toEqual([
      "ns1.example.net",
      "ns2.example.net",
    ]);
    expect(parseNameservers("  ")).toBeNull();
    expect(
      parseNameservers(Array.from({ length: 14 }, (_, i) => `ns${i}.x.net`).join("\n")),
    ).toBeNull();
  });

  it.each(["example.com", "café.fr", " shop.co.uk "])("accepts the name %j", (name) => {
    expect(looksLikeDomain(name)).toBe(true);
  });

  it.each(["", "example", ".com", "a b.com", "x/y.com", `${"a".repeat(250)}.com`])(
    "refuses the name %j",
    (name) => {
      expect(looksLikeDomain(name)).toBe(false);
    },
  );

  it("checks the owner of a registration", () => {
    expect(invalidContactFields(OWNER)).toEqual(new Set());
    expect(invalidContactFields(EMPTY_CONTACT)).toEqual(
      new Set(["given", "family", "streetaddr", "city", "zip", "email", "country"]),
    );
    expect(
      invalidContactFields({ ...OWNER, type: "company", phone: "0123", country: "FRA" }),
    ).toEqual(new Set(["orgname", "phone", "country"]));
    expect(invalidContactFields({ ...OWNER, phone: "+33.123456789" })).toEqual(new Set());
  });
});
