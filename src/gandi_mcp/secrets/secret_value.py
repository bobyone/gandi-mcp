# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of a secret typed by the user, such as an authorization code."""

import hmac
import unicodedata
from typing import NoReturn

from gandi_mcp.secrets.exceptions import InvalidSecretValueError

MAX_SECRET_LENGTH = 1024
MASK = "********"


class SecretValue:
    """A secret typed by the user on a local page, never shown nor serialized.

    ``repr`` and ``str`` are masked so that the value never reaches a log, a message
    or the model; :meth:`reveal` is only called to send it to Gandi.
    """

    __slots__ = ("_value",)

    def __init__(self, value: str, max_length: int = MAX_SECRET_LENGTH) -> None:
        """Validate a secret.

        Raises:
            InvalidSecretValueError: if it is empty, longer than ``max_length``, or has
                control characters.
        """
        if not value or len(value) > max_length:
            raise InvalidSecretValueError(f"a secret has 1 to {max_length} characters")
        if any(unicodedata.category(character).startswith("C") for character in value):
            raise InvalidSecretValueError("a secret has no control character")
        self._value = value

    def reveal(self) -> str:
        """Return the secret value."""
        return self._value

    def __repr__(self) -> str:
        return f"SecretValue({MASK})"

    __str__ = __repr__

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SecretValue):
            return NotImplemented
        return hmac.compare_digest(self._value.encode(), other._value.encode())

    def __hash__(self) -> int:
        return hash(self._value)

    def __reduce__(self) -> NoReturn:
        raise TypeError("a secret cannot be serialized")
