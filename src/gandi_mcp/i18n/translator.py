# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Abstraction of the message translation."""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from decimal import Decimal

from gandi_mcp.i18n.message import Message

SOURCE_LOCALE = "en"


class Translator(ABC):
    """Render messages in the user's language.

    Locale identifiers use the CLDR form with underscores (``fr``, ``sr_Latn``).
    """

    @property
    @abstractmethod
    def default_locale(self) -> str:
        """Locale used when none is given: the system language, or English."""

    @abstractmethod
    def negotiate(self, preferred: Iterable[str]) -> str:
        """Return the best supported locale for tags in preference order.

        Tags may use hyphens or underscores (``fr-CA``, ``sr_Latn``). Falls back to
        English when no tag matches.
        """

    @abstractmethod
    def translate(self, message: Message, locale: str | None = None, **params: object) -> str:
        """Render a message with its named parameters.

        Numbers are formatted for the locale. A plural message requires an
        integer ``count`` parameter.

        Raises:
            TranslationError: if a parameter is missing or ``count`` is invalid.
        """

    @abstractmethod
    def format_money(self, amount: Decimal, currency: str, locale: str | None = None) -> str:
        """Render an amount in a currency (ISO 4217 code) for the locale.

        Raises:
            TranslationError: if the currency code is unknown.
        """
