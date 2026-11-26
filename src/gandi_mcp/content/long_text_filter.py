# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Withhold long external texts from the model (free input policy)."""

import re

from gandi_mcp.gandi.gandi_response import JsonValue

WITHHELD = "long_text"
# Technical values that are long by nature and hold no free text: they are kept when
# they only contain base64 or hexadecimal characters.
TECHNICAL_FIELDS = frozenset({"public_key", "digest"})
TECHNICAL_VALUE = re.compile(r"^[A-Za-z0-9+/=]+$")


class LongTextFilter:
    """Replace every text longer than ``max_length`` characters by a placeholder.

    External free text is never passed to the model when it exceeds the limit
    (``content.max_free_input``): it may carry prompt injection that a short notice
    cannot contain. The placeholder tells its length; the text itself stays out of
    the conversation (the MCP App may show it).
    """

    def __init__(self, max_length: int) -> None:
        """Raises ValueError if ``max_length`` is not positive."""
        if max_length < 1:
            raise ValueError("max_length must be positive")
        self._max_length = max_length

    def allows(self, text: str) -> bool:
        """Tell whether an external text may be passed to the model as is."""
        return len(text) <= self._max_length

    def apply(self, data: JsonValue, key: str | None = None) -> JsonValue:
        """Return a copy of ``data`` with its long texts withheld, at any depth."""
        if isinstance(data, list):
            return [self.apply(item, key) for item in data]
        if isinstance(data, dict):
            return {name: self.apply(value, name) for name, value in data.items()}
        if isinstance(data, str) and not self.allows(data):
            if key in TECHNICAL_FIELDS and TECHNICAL_VALUE.match(data):
                return data
            return {"withheld": WITHHELD, "length": len(data)}
        return data
