// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import { describe, expect, it } from "vitest";
import { isRecordName, MAX_VALUES, parseTtl, parseValues } from "../../src/api/livedns";

describe("parseValues", () => {
  it("keeps one trimmed value per non-empty line, without duplicates", () => {
    expect(parseValues(' "a b" \r\n\n"c"\n"a b"\n')).toEqual(['"a b"', '"c"']);
  });

  it("refuses no value, too many values and non-printable or non-ASCII ones", () => {
    expect(parseValues(" \n ")).toBeNull();
    expect(
      parseValues(Array.from({ length: MAX_VALUES + 1 }, (_, i) => `v${i}`).join("\n")),
    ).toBeNull();
    expect(parseValues("café")).toBeNull();
    expect(parseValues("a\tb")).toBeNull();
    expect(parseValues("x".repeat(16_385))).toBeNull();
  });
});

describe("parseTtl", () => {
  it("accepts the LiveDNS bounds and empty for the default", () => {
    expect(parseTtl(" ")).toBeNull();
    expect(parseTtl("300")).toBe(300);
    expect(parseTtl("2592000")).toBe(2_592_000);
  });

  it("refuses values out of bounds or not whole numbers", () => {
    for (const text of ["299", "2592001", "3e2", "-300", "300.5", "abc"]) {
      expect(parseTtl(text)).toBeUndefined();
    }
  });
});

describe("isRecordName", () => {
  it("accepts names without spaces, up to 255 characters", () => {
    expect(isRecordName("@")).toBe(true);
    expect(isRecordName(" www ")).toBe(true);
    expect(isRecordName("default._domainkey")).toBe(true);
    expect(isRecordName("")).toBe(false);
    expect(isRecordName("two words")).toBe(false);
    expect(isRecordName("a".repeat(256))).toBe(false);
  });
});
