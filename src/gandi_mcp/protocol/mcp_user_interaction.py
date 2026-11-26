# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""User interaction through MCP elicitation, for one tool call."""

import uuid
from typing import Any

from mcp.server.elicitation import AcceptedElicitation, AcceptedUrlElicitation
from mcp.server.mcpserver import Context
from mcp_types.version import is_version_at_least
from pydantic import BaseModel, Field

from gandi_mcp.interaction.user_interaction import UserInteraction


class ConfirmationAnswer(BaseModel):
    """The form shown to the user: one checkbox."""

    confirm: bool = Field(default=False, description="Check to confirm the operation.")


# From this protocol revision, a tool cannot send requests to the client during a call:
# elicitation goes through input-required results, not supported yet (ADR 4).
INPUT_REQUIRED_VERSION = "2026-07-28"


class McpUserInteraction(UserInteraction):
    """Ask the user through the MCP client of the current call.

    Form elicitation is assumed when the client declares the capability without
    modes (protocol versions before URL mode). On protocol revisions without
    requests from the server during a call, nothing is supported, so that the
    confirmation falls back to a local page.
    """

    def __init__(self, context: Context[Any, Any]) -> None:
        self._context = context
        capabilities = context.client_capabilities
        elicitation = capabilities.elicitation if capabilities is not None else None
        version = context.protocol_version
        if version is not None and is_version_at_least(version, INPUT_REQUIRED_VERSION):
            elicitation = None
        self._form = elicitation is not None and (
            elicitation.form is not None or elicitation.url is None
        )
        self._url = elicitation is not None and elicitation.url is not None

    @property
    def supports_confirmation(self) -> bool:
        return self._form

    @property
    def supports_links(self) -> bool:
        return self._url

    async def confirm(self, message: str) -> bool:
        result = await self._context.elicit(message, ConfirmationAnswer)
        return isinstance(result, AcceptedElicitation) and result.data.confirm

    async def open_link(self, message: str, url: str) -> bool:
        result = await self._context.elicit_url(message, url, uuid.uuid4().hex)
        return isinstance(result, AcceptedUrlElicitation)
