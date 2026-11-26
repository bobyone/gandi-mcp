# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Abstraction of an operation: one call to Gandi on behalf of an account (Command)."""

import json
from abc import ABC, abstractmethod
from collections.abc import Mapping

from gandi_mcp.accounts.environment import Environment
from gandi_mcp.gandi.gandi_client import GandiClient
from gandi_mcp.gandi.gandi_response import GandiResponse, JsonValue
from gandi_mcp.i18n.localized_text import LocalizedText
from gandi_mcp.operations.operation_category import OperationCategory
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken


class Operation(ABC):
    """A Gandi call with its category and its description, run by the executor.

    Subclasses validate their parameters in their constructor.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Stable identifier of the operation, for example ``domain.renew``."""

    @property
    @abstractmethod
    def category(self) -> OperationCategory:
        """Read, write, destructive or billable."""

    @abstractmethod
    def parameters(self) -> Mapping[str, JsonValue]:
        """The parameters that define what the operation does."""

    @abstractmethod
    def describe(self) -> LocalizedText:
        """Readable description, shown when the user is asked to confirm."""

    @abstractmethod
    async def execute(
        self, client: GandiClient, environment: Environment, token: PersonalAccessToken
    ) -> GandiResponse:
        """Call Gandi.

        Raises:
            GandiError: if Gandi refuses or cannot be reached.
        """

    def subject(self) -> str:
        """Fingerprint of the operation and its parameters, for confirmations."""
        return self.name + ":" + json.dumps(self.parameters(), sort_keys=True, default=str)
