// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import { describe, expect, it } from "vitest";
import { CATALOGS, createI18n, negotiate } from "../../src/i18n/i18n";

describe("negotiate", () => {
  it.each([
    [["fr-CA"], "fr"],
    [["sr-Latn-RS"], "sr-Latn"],
    [["sr"], "sr-Cyrl"],
    [["no"], "nb"],
    [["sr_Latn"], "sr-Latn"],
    [[undefined, " ", "not a tag!", "pl"], "pl"],
    [["xx"], "en"],
    [[], "en"],
  ])("picks %j as %s", (tags, expected) => {
    expect(negotiate(tags)).toBe(expected);
  });
});

describe("createI18n", () => {
  it("renders ICU plurals in the chosen language", async () => {
    const english = await createI18n("en");
    const polish = await createI18n("pl");

    expect(english.t("accounts.count", { count: 0 })).toBe("No account");
    expect(english.t("accounts.count", { count: 1 })).toBe("1 account");
    expect(english.t("accounts.count", { count: 3 })).toBe("3 accounts");
    expect(polish.language).toBe("pl");
    expect(polish.t("accounts.count", { count: 5 })).not.toBe("5 accounts");
  });

  it("has a catalog per target language", () => {
    expect(Object.keys(CATALOGS)).toHaveLength(43);
  });
});
