# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Translator rendering every message in English, its source language."""

from collections.abc import Iterable

from gandi_mcp.i18n.message import Message
from gandi_mcp.i18n.translator import SOURCE_LOCALE, Translator


class SourceTranslator(Translator):
    """Render the English source; records the locales it was asked for."""

    def __init__(self) -> None:
        self.locales: list[str | None] = []

    @property
    def default_locale(self) -> str:
        return SOURCE_LOCALE

    def negotiate(self, preferred: Iterable[str]) -> str:
        return SOURCE_LOCALE

    def translate(self, message: Message, locale: str | None = None, **params: object) -> str:
        self.locales.append(locale)
        count = params.get("count")
        text = message.plural if message.plural and count != 1 else message.singular
        return text.format(**params)
