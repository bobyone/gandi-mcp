# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of a page of a Gandi list."""

from dataclasses import dataclass

from gandi_mcp.domains.exceptions import InvalidDomainInputError

MAX_PAGE = 1000
MAX_PER_PAGE = 100


@dataclass(frozen=True)
class PageRequest:
    """Which page of a list to read: ``page`` from 1, ``per_page`` items (1 to 100)."""

    page: int = 1
    per_page: int = 25

    def __post_init__(self) -> None:
        if not 1 <= self.page <= MAX_PAGE:
            raise InvalidDomainInputError(f"page is between 1 and {MAX_PAGE}")
        if not 1 <= self.per_page <= MAX_PER_PAGE:
            raise InvalidDomainInputError(f"per_page is between 1 and {MAX_PER_PAGE}")

    def query(self) -> dict[str, int]:
        """Query parameters of the page."""
        return {"page": self.page, "per_page": self.per_page}
