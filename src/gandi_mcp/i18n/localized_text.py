# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""A message with its parameters, rendered later in the user's language."""

from collections.abc import Mapping
from dataclasses import dataclass, field

from gandi_mcp.i18n.message import Message


@dataclass(frozen=True)
class LocalizedText:
    """A message and its named parameters, translated when displayed."""

    message: Message
    params: Mapping[str, object] = field(default_factory=dict)
