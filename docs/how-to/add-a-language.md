<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Add a language or fix a translation

Server messages use gettext catalogs in
[`src/gandi_mcp/locales/`](../../src/gandi_mcp/locales/): one
`<locale>/LC_MESSAGES/messages.po` per language, generated from the template
`messages.pot`. The target locales are declared in
[`locales.toml`](../../src/gandi_mcp/locales/locales.toml). English is the
source language and has no catalog. Adding a language needs no code change.

The MCP App has its own ICU catalogs in
[`ui/src/i18n/locales/`](../../ui/src/i18n/locales/): one `<tag>.json` per
language, named with the BCP 47 tag (`sr-Latn`), with the same keys as
`en.json`.

## Add a language

1. Choose its locale identifier as understood by Babel (CLDR), for example
   `pt`, `sr_Latn`, `nn`.
2. Add it to the `supported` list of `src/gandi_mcp/locales/locales.toml`.
3. Create its catalog:

   ```text
   uv run pybabel init -i src/gandi_mcp/locales/messages.pot -d src/gandi_mcp/locales -l <locale>
   ```

4. Translate every entry. Keep named parameters (`{name}`) unchanged in every
   plural form given by the catalog header.
5. Add a translator comment `# needs-review` to each entry until a native
   speaker validates it, then remove it.
6. Copy `ui/src/i18n/locales/en.json` to `<tag>.json`, translate every value
   (keep the ICU arguments such as `{name}` and the plural categories of the
   language, with an `other` form), and add the tag to
   `ui/src/i18n/needs-review.json`.
7. Run `uv run python scripts/check_translations.py` and
   `uv run python scripts/check_ui_translations.py`, then rebuild the App
   (`npm --prefix ui run build`).
8. Add the labels of the displayed terms to the glossary.

## Fix a translation

Edit the entry in the language's `messages.po` (server messages) or
`ui/src/i18n/locales/<tag>.json` (MCP App). If you are a native speaker,
remove its `# needs-review` comment, or the language from
`ui/src/i18n/needs-review.json` once the whole catalog is reviewed. Run the
translation checks and open a pull request as described in
[CONTRIBUTING.md](../../CONTRIBUTING.md).

## After changing messages in the code

```text
uv run pybabel extract -F babel.cfg --no-location -o src/gandi_mcp/locales/messages.pot .
uv run pybabel update -i src/gandi_mcp/locales/messages.pot -d src/gandi_mcp/locales --no-fuzzy-matching --ignore-obsolete
```

Then translate the new entries in every language.
