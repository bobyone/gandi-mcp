// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import { describe, expect, it } from "vitest";
import { isValidName, isValidToken } from "../../src/api/account";

describe("account values", () => {
  it.each(["Perso", "Société 2", "my-shop", "Работа", "a".repeat(40)])("accepts %s", (name) => {
    expect(isValidName(name)).toBe(true);
  });

  it.each(["", "   ", "a".repeat(41), "two  spaces", "under_score", "-start"])(
    "refuses %j",
    (name) => {
      expect(isValidName(name)).toBe(false);
    },
  );

  it("checks the token format", () => {
    expect(isValidToken("pat_0123456789abcdef")).toBe(true);
    expect(isValidToken("short")).toBe(false);
    expect(isValidToken("pat_0123456789 abcdef")).toBe(false);
    expect(isValidToken("x".repeat(513))).toBe(false);
  });
});
