# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Operation reading the identity behind the token of an account."""

from collections.abc import Mapping

from gandi_mcp.accounts.environment import Environment
from gandi_mcp.gandi.gandi_client import GandiClient
from gandi_mcp.gandi.gandi_response import GandiResponse, JsonValue
from gandi_mcp.i18n.localized_text import LocalizedText
from gandi_mcp.i18n.message import N_
from gandi_mcp.operations.confirmation_answer import ConfirmationAnswer
from gandi_mcp.operations.operation import Operation
from gandi_mcp.operations.operation_category import OperationCategory
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken

DESCRIPTION = N_("read the identity of the account")


class VerifyIdentity(Operation):
    """``GET organization/user-info``: who Gandi recognizes behind the token."""

    @property
    def name(self) -> str:
        return "organization.user_info"

    @property
    def category(self) -> OperationCategory:
        return OperationCategory.READ

    def parameters(self) -> Mapping[str, JsonValue]:
        return {}

    def describe(self) -> LocalizedText:
        return LocalizedText(DESCRIPTION)

    async def execute(
        self,
        client: GandiClient,
        environment: Environment,
        token: PersonalAccessToken,
        answer: ConfirmationAnswer | None = None,
    ) -> GandiResponse:
        return await client.request(environment, token, "GET", ("organization", "user-info"))
