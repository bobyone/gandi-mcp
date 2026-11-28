// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

/** A date stored in UTC, shown in the user's language and time zone; null if invalid. */
export function formatDate(iso: string | null, language: string): string | null {
  if (iso === null) return null;
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return null;
  return new Intl.DateTimeFormat(language, { dateStyle: "medium" }).format(date);
}

/** An amount in the user's language; null when the currency is not a valid code. */
export function formatPrice(amount: number, currency: string, language: string): string | null {
  try {
    return new Intl.NumberFormat(language, { style: "currency", currency }).format(amount);
  } catch {
    return null;
  }
}

/** A date and time stored in UTC, shown in the user's language and time zone; null if invalid. */
export function formatDateTime(iso: string | null, language: string): string | null {
  if (iso === null) return null;
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return null;
  return new Intl.DateTimeFormat(language, { dateStyle: "medium", timeStyle: "short" }).format(
    date,
  );
}
