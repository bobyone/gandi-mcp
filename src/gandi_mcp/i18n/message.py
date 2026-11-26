# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Translatable messages and the markers that declare them for extraction."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Message:
    """A user-facing message in English, the source language.

    Named parameters are written ``{name}``. A plural message is chosen by its
    ``count`` parameter, following the plural rules of each language.
    """

    singular: str
    plural: str | None = None

    @property
    def is_plural(self) -> bool:
        """Tell whether the message has plural forms."""
        return self.plural is not None


def N_(text: str) -> Message:  # noqa: N802 - gettext extraction keyword
    """Declare a singular message (extracted by Babel's ``N_`` keyword)."""
    return Message(text)


def ngettext(singular: str, plural: str) -> Message:
    """Declare a plural message (extracted by Babel's ``ngettext`` keyword)."""
    return Message(singular, plural)
