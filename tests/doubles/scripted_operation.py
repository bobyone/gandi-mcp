# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Operation of a chosen category calling a fixed Gandi path."""

from collections.abc import Mapping
from dataclasses import dataclass, field

from gandi_mcp.accounts.environment import Environment
from gandi_mcp.confirmation.confirmation_option import ConfirmationOption
from gandi_mcp.confirmation.secret_input import SecretInput
from gandi_mcp.gandi.gandi_client import GandiClient
from gandi_mcp.gandi.gandi_response import GandiResponse, JsonValue
from gandi_mcp.i18n.localized_text import LocalizedText
from gandi_mcp.i18n.message import Message
from gandi_mcp.operations.confirmation_answer import ConfirmationAnswer
from gandi_mcp.operations.operation import Operation
from gandi_mcp.operations.operation_category import OperationCategory
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from gandi_mcp.secrets.secret_value import SecretValue


@dataclass
class ScriptedOperation(Operation):
    """``DELETE test/<target>`` or similar, with the category under test."""

    operation_category: OperationCategory
    target: str = "example.com"
    method: str = "DELETE"
    executed: list[Environment] = field(default_factory=list)
    secret_label: Message | None = None
    secrets: list[SecretValue | None] = field(default_factory=list)
    answers: list[ConfirmationAnswer | None] = field(default_factory=list)
    option: ConfirmationOption | None = None
    prepared: int = 0

    @property
    def name(self) -> str:
        return "test.operation"

    @property
    def category(self) -> OperationCategory:
        return self.operation_category

    def parameters(self) -> Mapping[str, JsonValue]:
        return {"target": self.target}

    def confirmation_option(self) -> ConfirmationOption | None:
        return self.option

    async def prepare(
        self, client: GandiClient, environment: Environment, token: PersonalAccessToken
    ) -> None:
        self.prepared += 1

    def secret_input(self) -> SecretInput | None:
        return SecretInput(self.secret_label, 64) if self.secret_label is not None else None

    def describe(self) -> LocalizedText:
        return LocalizedText(Message("delete {target}"), {"target": self.target})

    async def execute(
        self,
        client: GandiClient,
        environment: Environment,
        token: PersonalAccessToken,
        answer: ConfirmationAnswer | None = None,
    ) -> GandiResponse:
        self.executed.append(environment)
        self.secrets.append(answer.secret if answer is not None else None)
        self.answers.append(answer)
        return await client.request(environment, token, self.method, ("test", self.target))
