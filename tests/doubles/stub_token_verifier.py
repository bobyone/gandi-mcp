# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Token verifier accepting configured tokens per environment."""

from dataclasses import dataclass, field

from gandi_mcp.accounts.account_identity import AccountIdentity
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.accounts.exceptions import TokenRejectedError
from gandi_mcp.accounts.token_verifier import TokenVerifier
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken


@dataclass
class StubTokenVerifier(TokenVerifier):
    """Accept the tokens listed for an environment; ``failure`` is raised when set."""

    accepted: dict[Environment, set[str]] = field(default_factory=dict)
    failure: Exception | None = None
    calls: list[Environment] = field(default_factory=list)

    def accept(self, environment: Environment, token: PersonalAccessToken) -> None:
        self.accepted.setdefault(environment, set()).add(token.reveal())

    async def verify(self, environment: Environment, token: PersonalAccessToken) -> AccountIdentity:
        self.calls.append(environment)
        if self.failure is not None:
            raise self.failure
        if token.reveal() not in self.accepted.get(environment, set()):
            raise TokenRejectedError(f"rejected in {environment.value}")
        return AccountIdentity("ada", "Ada Lovelace")
