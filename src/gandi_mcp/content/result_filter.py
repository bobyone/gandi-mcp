# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Abstraction of a filter applied to Gandi data before it reaches the model."""

from abc import ABC, abstractmethod

from gandi_mcp.content.disclosure import Disclosure
from gandi_mcp.gandi.gandi_response import JsonValue


class ResultFilter(ABC):
    """Rewrite Gandi data shown to the model (ADR 10); filters are chained in order."""

    @abstractmethod
    def filter(self, data: JsonValue, disclosure: Disclosure) -> JsonValue:
        """Return a filtered copy of ``data``, at any depth; ``data`` is not changed."""
