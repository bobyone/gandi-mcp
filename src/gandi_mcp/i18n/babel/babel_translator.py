# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Translator reading the gettext catalogs with Babel, compiled in memory."""

import gettext
import io
import logging
import tomllib
from collections.abc import Iterable, Mapping
from pathlib import Path
from string import Formatter

from babel import Locale, UnknownLocaleError
from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po
from babel.numbers import format_decimal

from gandi_mcp.i18n.exceptions import TranslationError
from gandi_mcp.i18n.message import Message
from gandi_mcp.i18n.translator import SOURCE_LOCALE, Translator

LOCALES_FILE = "locales.toml"
CATALOG = Path("LC_MESSAGES") / "messages.po"
# A language without its own catalog uses the closest one.
FALLBACKS: Mapping[str, str] = {"cnr": "sr_Latn", "sr": "sr_Cyrl", "no": "nb"}

logger = logging.getLogger(__name__)


def default_locales_directory() -> Path:
    """Return the catalogs shipped with the package."""
    return Path(__file__).resolve().parents[2] / "locales"


class BabelTranslator(Translator):
    """Translate with the ``<locale>/LC_MESSAGES/messages.po`` catalogs of a directory.

    Catalogs are read and compiled in memory once, at construction. Unknown locales
    fall back to English, the source language.
    """

    def __init__(self, locales_directory: Path, default_locale: str | None = None) -> None:
        """Load the catalogs of the locales declared in ``locales.toml``.

        Raises:
            TranslationError: if the declaration or a catalog cannot be read.
        """
        self._catalogs = {
            locale: self._compile(locales_directory / locale / CATALOG)
            for locale in self._declared(locales_directory)
        }
        self._by_lower = {locale.lower(): locale for locale in self._catalogs}
        self._default = self.negotiate([default_locale] if default_locale else [])

    @property
    def default_locale(self) -> str:
        return self._default

    @property
    def supported_locales(self) -> tuple[str, ...]:
        """Locales with a catalog, plus English."""
        return (SOURCE_LOCALE, *sorted(self._catalogs))

    def negotiate(self, preferred: Iterable[str]) -> str:
        for tag in preferred:
            found = self._match(tag.strip().replace("-", "_"))
            if found:
                return found
        return SOURCE_LOCALE

    def translate(self, message: Message, locale: str | None = None, **params: object) -> str:
        chosen = self.negotiate([locale]) if locale else self._default
        translations = self._catalogs.get(chosen, gettext.NullTranslations())
        if message.plural is None:
            text = translations.gettext(message.singular)
        else:
            count = params.get("count")
            if isinstance(count, bool) or not isinstance(count, int):
                raise TranslationError("a plural message needs an integer count parameter")
            text = translations.ngettext(message.singular, message.plural, count)
        return self._format(text, chosen, params)

    def _match(self, tag: str) -> str | None:
        if not tag:
            return None
        exact = self._by_lower.get(tag.lower())
        if exact:
            return exact
        try:
            parsed = Locale.parse(tag)
        except (UnknownLocaleError, ValueError):
            return None
        candidates = (
            f"{parsed.language}_{parsed.script}" if parsed.script else None,
            parsed.language,
            FALLBACKS.get(parsed.language),
        )
        for candidate in candidates:
            if candidate and candidate.lower() in self._by_lower:
                return self._by_lower[candidate.lower()]
        if parsed.language == SOURCE_LOCALE:
            return SOURCE_LOCALE
        return None

    @staticmethod
    def _format(text: str, locale: str, params: Mapping[str, object]) -> str:
        values = {
            name: format_decimal(value, locale=locale)
            if isinstance(value, int | float) and not isinstance(value, bool)
            else value
            for name, value in params.items()
        }
        required = {field for _, field, _, _ in Formatter().parse(text) if field}
        missing = sorted(required - values.keys())
        if missing:
            raise TranslationError(f"missing message parameters: {', '.join(missing)}")
        return text.format_map(values)

    @staticmethod
    def _declared(directory: Path) -> list[str]:
        try:
            with (directory / LOCALES_FILE).open("rb") as stream:
                declared = tomllib.load(stream).get("supported", [])
        except (OSError, tomllib.TOMLDecodeError) as error:
            raise TranslationError(f"cannot read {LOCALES_FILE}") from error
        if not isinstance(declared, list) or not all(isinstance(i, str) for i in declared):
            raise TranslationError(f"{LOCALES_FILE}: 'supported' must be a list of locales")
        return declared

    @staticmethod
    def _compile(path: Path) -> gettext.GNUTranslations:
        try:
            with path.open("rb") as stream:
                catalog = read_po(stream)
        except (OSError, ValueError) as error:
            raise TranslationError(f"cannot read catalog {path.parent.parent.name}") from error
        compiled = io.BytesIO()
        write_mo(compiled, catalog)
        compiled.seek(0)
        logger.debug("catalog %s loaded", path.parent.parent.name)
        return gettext.GNUTranslations(compiled)
