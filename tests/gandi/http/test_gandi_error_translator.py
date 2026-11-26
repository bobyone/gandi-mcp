# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the translation of Gandi error responses."""

import pytest

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
from gandi_mcp.gandi.http.gandi_error_translator import (
    MAX_DETAILS,
    MAX_RETRY_AFTER,
    extract_details,
    translate_error,
)


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (400, GandiValidationError),
        (401, GandiAuthenticationError),
        (403, GandiPermissionError),
        (404, GandiNotFoundError),
        (409, GandiConflictError),
        (422, GandiValidationError),
        (429, GandiRateLimitError),
        (500, GandiUnavailableError),
        (503, GandiUnavailableError),
        (418, GandiUnexpectedResponseError),
        (302, GandiUnexpectedResponseError),
    ],
)
def test_maps_status_codes(status: int, expected: type[GandiError]) -> None:
    assert type(translate_error(status, None)) is expected


def test_keeps_gandi_explanations() -> None:
    body: JsonValue = {
        "cause": "Bad Request",
        "code": 400,
        "message": "Invalid  request\n",
        "object": "HTTPBadRequest",
        "errors": [
            {"location": "body", "name": "fqdn", "description": "is not a valid domain"},
            {"location": "body", "description": "missing owner"},
            "noise",
            {"location": "body"},
        ],
    }

    error = translate_error(400, body)

    assert error.details == ("Invalid request", "fqdn: is not a valid domain", "missing owner")


@pytest.mark.parametrize("body", [None, "text", [1], {"message": 3, "errors": "x"}])
def test_ignores_unusable_bodies(body: JsonValue) -> None:
    assert extract_details(body) == ()


def test_bounds_the_explanations() -> None:
    body: JsonValue = {
        "message": "x" * 5000,
        "errors": [{"description": str(index)} for index in range(MAX_DETAILS * 2)],
    }

    details = extract_details(body)

    assert len(details) == MAX_DETAILS
    assert len(details[0]) == 5000  # never truncated: the presenter withholds it


@pytest.mark.parametrize(
    ("header", "expected"), [("12", 12), ("99999", MAX_RETRY_AFTER), ("soon", None), (None, None)]
)
def test_reads_retry_after(header: str | None, expected: int | None) -> None:
    headers = {"retry-after": header} if header is not None else {}

    error = translate_error(429, None, headers)

    assert isinstance(error, GandiRateLimitError)
    assert error.retry_after == expected
