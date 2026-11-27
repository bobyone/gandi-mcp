// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import { describe, expect, it } from "vitest";
import { formatDate, formatPrice } from "../../../src/components/domains/format";

describe("format", () => {
  it("formats dates in the user's language", () => {
    expect(formatDate("2027-03-01T12:00:00Z", "en")).toBe(
      new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(
        new Date("2027-03-01T12:00:00Z"),
      ),
    );
    expect(formatDate(null, "en")).toBeNull();
    expect(formatDate("not a date", "en")).toBeNull();
  });

  it("formats prices in the user's language", () => {
    expect(formatPrice(12.5, "EUR", "fr")).toBe(
      new Intl.NumberFormat("fr", { style: "currency", currency: "EUR" }).format(12.5),
    );
    expect(formatPrice(1, "not a currency", "en")).toBeNull();
  });
});
