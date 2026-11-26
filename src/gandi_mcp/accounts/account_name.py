# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of an account name."""

import unicodedata
from dataclasses import dataclass, field

from gandi_mcp.accounts.exceptions import InvalidAccountNameError

MAX_LENGTH = 40
ALLOWED_PUNCTUATION = frozenset("- ")


def _allowed(character: str) -> bool:
    return character.isalnum() or character in ALLOWED_PUNCTUATION


@dataclass(frozen=True, order=False)
class AccountName:
    """A short name chosen by the user: letters, digits, hyphens and single spaces.

    The value is normalized (NFC, surrounding spaces removed). Two names are equal
    when they only differ by case.
    """

    value: str
    key: str = field(init=False, repr=False, compare=True)

    def __post_init__(self) -> None:
        normalized = unicodedata.normalize("NFC", self.value).strip()
        if not normalized or len(normalized) > MAX_LENGTH:
            raise InvalidAccountNameError(f"an account name has 1 to {MAX_LENGTH} characters")
        if not all(_allowed(character) for character in normalized) or "  " in normalized:
            raise InvalidAccountNameError(
                "an account name only has letters, digits, hyphens and single spaces"
            )
        object.__setattr__(self, "value", normalized)
        object.__setattr__(self, "key", normalized.casefold())

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AccountName):
            return NotImplemented
        return self.key == other.key

    def __hash__(self) -> int:
        return hash(self.key)
