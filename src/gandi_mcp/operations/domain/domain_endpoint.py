# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Declarative specification of one endpoint of the Gandi Domain API."""

import re
from dataclasses import dataclass, field

from gandi_mcp.i18n.message import Message
from gandi_mcp.operations.operation_category import OperationCategory

METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE"})
PLACEHOLDER = re.compile(r"^\{([a-z_]+)\}$")


@dataclass(frozen=True)
class DomainEndpoint:
    """What an endpoint does and how to call it.

    Attributes:
        name: Stable identifier, also the name of its tool (``domain_list``).
        method: HTTP method.
        path: Path segments below the API base URL; ``{name}`` segments are filled
            with validated values.
        category: Read, write, destructive or billable.
        query: Query parameters the endpoint accepts; any other one is refused.
        description: What the user confirms; required for confirmed categories.
        supports_dry_run: Whether Gandi accepts the ``Dry-Run`` header.
        follow_up: Name of the tool following the resulting asynchronous operation.
    """

    name: str
    method: str
    path: tuple[str, ...]
    category: OperationCategory
    query: frozenset[str] = field(default_factory=frozenset)
    description: Message | None = None
    supports_dry_run: bool = False
    follow_up: str | None = None

    def __post_init__(self) -> None:
        if self.method not in METHODS:
            raise ValueError(f"{self.name}: unsupported method {self.method}")
        if not self.path:
            raise ValueError(f"{self.name}: empty path")
        if self.category.needs_confirmation and self.description is None:
            raise ValueError(f"{self.name}: a confirmed endpoint needs a description")

    @property
    def placeholders(self) -> tuple[str, ...]:
        """Names of the path segments to fill, in order."""
        return tuple(
            match.group(1) for segment in self.path if (match := PLACEHOLDER.match(segment))
        )
