# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object describing how the user can be reached for one call."""

from dataclasses import dataclass

from gandi_mcp.interaction.user_interaction import UserInteraction


@dataclass(frozen=True)
class ConfirmationContext:
    """The ways to reach the user during one tool call.

    Attributes:
        interaction: Elicitation of the MCP client, when it supports some.
        locale: Language of the user, when known.
    """

    interaction: UserInteraction | None = None
    locale: str | None = None
