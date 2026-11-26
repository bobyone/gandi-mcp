// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import i18next, { type i18n as I18n } from "i18next";
import ICU from "i18next-icu";
import { initReactI18next } from "react-i18next";

type Catalog = Record<string, string>;

const modules = import.meta.glob<Catalog>("./locales/*.json", { eager: true, import: "default" });

/** Catalogs by BCP 47 tag (`fr`, `sr-Latn`); English is the source. */
export const CATALOGS: Readonly<Record<string, Catalog>> = Object.fromEntries(
  Object.entries(modules).map(([path, catalog]) => [
    path.replace("./locales/", "").replace(".json", ""),
    catalog,
  ]),
);
export const SOURCE_LANGUAGE = "en";
/** A language without its own catalog uses the closest one. */
const FALLBACKS: Readonly<Record<string, string>> = { sr: "sr-Cyrl", no: "nb", cnr: "sr-Latn" };

/** Return the best supported language for tags in preference order, else English. */
export function negotiate(preferred: readonly (string | undefined)[]): string {
  const supported = new Map(Object.keys(CATALOGS).map((tag) => [tag.toLowerCase(), tag]));
  for (const raw of preferred) {
    if (raw === undefined || raw.trim() === "") continue;
    let locale: Intl.Locale;
    try {
      locale = new Intl.Locale(raw.trim().replace("_", "-"));
    } catch {
      continue;
    }
    const candidates = [
      locale.baseName,
      locale.script ? `${locale.language}-${locale.script}` : undefined,
      locale.language,
      FALLBACKS[locale.language],
    ];
    for (const candidate of candidates) {
      const found = candidate ? supported.get(candidate.toLowerCase()) : undefined;
      if (found) return found;
    }
  }
  return SOURCE_LANGUAGE;
}

/** Create an i18next instance with ICU messages, in the chosen language. */
export async function createI18n(language: string): Promise<I18n> {
  const instance = i18next.createInstance();
  await instance
    .use(ICU)
    .use(initReactI18next)
    .init({
      lng: language,
      fallbackLng: SOURCE_LANGUAGE,
      resources: Object.fromEntries(
        Object.entries(CATALOGS).map(([tag, catalog]) => [tag, { translation: catalog }]),
      ),
      keySeparator: false,
      interpolation: { escapeValue: false },
      returnNull: false,
    });
  return instance;
}
