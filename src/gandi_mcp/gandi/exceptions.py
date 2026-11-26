# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Exceptions of the Gandi API access.

``details`` holds the explanations returned by Gandi: untrusted data, bounded in
length, never containing the token.
"""


class GandiError(Exception):
    """Base class of the Gandi errors."""

    def __init__(self, message: str, details: tuple[str, ...] = ()) -> None:
        super().__init__(message)
        self.details = details


class GandiAuthenticationError(GandiError):
    """Gandi refused the token (HTTP 401): invalid, revoked or expired."""


class GandiPermissionError(GandiError):
    """Gandi refused the operation (HTTP 403): missing right or expired token."""


class GandiNotFoundError(GandiError):
    """The Gandi resource does not exist (HTTP 404)."""


class GandiValidationError(GandiError):
    """Gandi refused the submitted data (HTTP 400 or 422)."""


class GandiConflictError(GandiError):
    """The operation conflicts with the state of the resource (HTTP 409)."""


class GandiRateLimitError(GandiError):
    """Too many requests (HTTP 429); ``retry_after`` is in seconds when known."""

    def __init__(
        self, message: str, details: tuple[str, ...] = (), retry_after: int | None = None
    ) -> None:
        super().__init__(message, details)
        self.retry_after = retry_after


class GandiUnavailableError(GandiError):
    """Gandi cannot be reached or failed (network error, timeout, HTTP 5xx)."""


class GandiUnexpectedResponseError(GandiError):
    """Gandi answered with a status or a body this client does not understand."""
