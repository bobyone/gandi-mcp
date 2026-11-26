# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of a successful Gandi response."""

from dataclasses import dataclass

type JsonValue = bool | int | float | str | list[JsonValue] | dict[str, JsonValue] | None


@dataclass(frozen=True)
class GandiResponse:
    """A successful answer of the Gandi API.

    Attributes:
        status: HTTP status code (2xx).
        data: Decoded JSON body, or ``None`` when the body is empty. Untrusted data.
        total_count: Total number of items of a paginated list, when given.
        location: URL of a created resource, when given.
    """

    status: int
    data: JsonValue
    total_count: int | None = None
    location: str | None = None
