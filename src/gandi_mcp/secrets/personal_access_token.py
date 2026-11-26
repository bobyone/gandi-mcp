# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object holding a Gandi Personal Access Token without ever showing it."""

import hmac
import string
from typing import NoReturn

from gandi_mcp.secrets.exceptions import InvalidTokenFormatError

MIN_LENGTH = 16
MAX_LENGTH = 512
ALLOWED_CHARACTERS = frozenset(string.ascii_letters + string.digits + string.punctuation)
MASK = "********"


class PersonalAccessToken:
    """A validated token: printable ASCII without whitespace, of bounded length.

    ``repr`` and ``str`` are masked so that a token never reaches a log or a message;
    :meth:`reveal` is only called to authenticate a request or to store the token.
    """

    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        """Validate a token.

        Raises:
            InvalidTokenFormatError: if the length or a character is not allowed.
        """
        if not MIN_LENGTH <= len(value) <= MAX_LENGTH:
            raise InvalidTokenFormatError(
                f"a token has between {MIN_LENGTH} and {MAX_LENGTH} characters"
            )
        if not set(value) <= ALLOWED_CHARACTERS:
            raise InvalidTokenFormatError("a token only has printable characters, no space")
        self._value = value

    def reveal(self) -> str:
        """Return the secret value."""
        return self._value

    def __repr__(self) -> str:
        return f"PersonalAccessToken({MASK})"

    __str__ = __repr__

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PersonalAccessToken):
            return NotImplemented
        return hmac.compare_digest(self._value, other._value)

    def __hash__(self) -> int:
        return hash(self._value)

    def __reduce__(self) -> NoReturn:
        raise TypeError("a Personal Access Token cannot be serialized")
