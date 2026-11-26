# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of a token entry session."""

from dataclasses import dataclass

from gandi_mcp.token_entry.token_entry_target import TokenEntryTarget


@dataclass(frozen=True)
class TokenEntrySession:
    """A time-limited chance to submit one token for a target account."""

    session_id: str
    target: TokenEntryTarget
    deadline: float
