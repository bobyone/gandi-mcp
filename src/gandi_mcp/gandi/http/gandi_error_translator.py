# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Translation of Gandi error responses into Gandi exceptions."""

from collections.abc import Mapping

from gandi_mcp.gandi.exceptions import (
    GandiAuthenticationError,
    GandiConflictError,
    GandiError,
    GandiNotFoundError,
    GandiPermissionError,
    GandiRateLimitError,
    GandiUnavailableError,
    GandiUnexpectedResponseError,
    GandiValidationError,
)
from gandi_mcp.gandi.gandi_response import JsonValue

MAX_DETAILS = 10
MAX_DETAIL_LENGTH = 300
MAX_RETRY_AFTER = 3600

_BY_STATUS: Mapping[int, tuple[type[GandiError], str]] = {
    400: (GandiValidationError, "Gandi refused the submitted data"),
    401: (GandiAuthenticationError, "Gandi refused the token"),
    403: (GandiPermissionError, "Gandi refused the operation for this token"),
    404: (GandiNotFoundError, "the Gandi resource does not exist"),
    409: (GandiConflictError, "the operation conflicts with the Gandi resource"),
    422: (GandiValidationError, "Gandi refused the submitted data"),
}


def _bounded(text: str) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= MAX_DETAIL_LENGTH:
        return cleaned
    return cleaned[: MAX_DETAIL_LENGTH - 1] + "\N{HORIZONTAL ELLIPSIS}"


def extract_details(body: JsonValue) -> tuple[str, ...]:
    """Collect the explanations of a Gandi error body (``message``, ``errors``)."""
    if not isinstance(body, dict):
        return ()
    details: list[str] = []
    message = body.get("message")
    if isinstance(message, str) and message.strip():
        details.append(message)
    errors = body.get("errors")
    for error in errors if isinstance(errors, list) else []:
        if not isinstance(error, dict):
            continue
        parts = [error.get("name"), error.get("description")]
        text = ": ".join(part for part in parts if isinstance(part, str) and part.strip())
        if text:
            details.append(text)
    return tuple(_bounded(detail) for detail in details[:MAX_DETAILS])


def _retry_after(value: str | None) -> int | None:
    if value is None or not value.strip().isdigit():
        return None
    return min(int(value), MAX_RETRY_AFTER)


def translate_error(
    status: int, body: JsonValue, headers: Mapping[str, str] | None = None
) -> GandiError:
    """Return the exception describing an unsuccessful Gandi response."""
    details = extract_details(body)
    if status == 429:  # noqa: PLR2004 - HTTP status
        retry = _retry_after((headers or {}).get("retry-after"))
        return GandiRateLimitError("too many requests to Gandi", details, retry)
    if status >= 500:  # noqa: PLR2004 - HTTP status class
        return GandiUnavailableError(f"Gandi failed with status {status}", details)
    known = _BY_STATUS.get(status)
    if known is not None:
        exception, message = known
        return exception(message, details)
    return GandiUnexpectedResponseError(f"unexpected Gandi status {status}", details)
