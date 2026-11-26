# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Gandi client replaying scripted outcomes and recording the calls."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from gandi_mcp.accounts.environment import Environment
from gandi_mcp.gandi.gandi_client import GandiClient, QueryValue
from gandi_mcp.gandi.gandi_response import GandiResponse, JsonValue
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken


@dataclass(frozen=True)
class RecordedCall:
    """One request received by the fake client."""

    environment: Environment
    token: PersonalAccessToken
    method: str
    path: tuple[str, ...]
    query: Mapping[str, QueryValue] | None
    body: JsonValue
    accept_see_other: bool = False


@dataclass
class FakeGandiClient(GandiClient):
    """Return the next scripted outcome: a response, or an exception to raise."""

    outcomes: list[GandiResponse | Exception] = field(default_factory=list)
    calls: list[RecordedCall] = field(default_factory=list)
    closed: bool = False

    async def request(
        self,
        environment: Environment,
        token: PersonalAccessToken,
        method: str,
        path: Sequence[str],
        *,
        query: Mapping[str, QueryValue] | None = None,
        body: JsonValue = None,
        accept_see_other: bool = False,
    ) -> GandiResponse:
        self.calls.append(
            RecordedCall(environment, token, method, tuple(path), query, body, accept_see_other)
        )
        outcome = self.outcomes.pop(0) if self.outcomes else GandiResponse(200, None)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    async def close(self) -> None:
        self.closed = True
