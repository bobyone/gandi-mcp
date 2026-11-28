# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""A destructive change of the records of a zone, confirmed with its counted effect."""

from collections.abc import Mapping

from gandi_mcp.accounts.environment import Environment
from gandi_mcp.confirmation.confirmation_option import ConfirmationOption
from gandi_mcp.domains.domain_name import DomainName
from gandi_mcp.gandi.exceptions import GandiError
from gandi_mcp.gandi.gandi_client import GandiClient
from gandi_mcp.gandi.gandi_response import GandiResponse, JsonValue
from gandi_mcp.i18n.localized_text import LocalizedText
from gandi_mcp.i18n.message import Message
from gandi_mcp.operations.confirmation_answer import ConfirmationAnswer
from gandi_mcp.operations.endpoint.endpoint import Endpoint
from gandi_mcp.operations.endpoint.endpoint_operation import EndpointOperation
from gandi_mcp.operations.livedns import livedns_endpoints
from gandi_mcp.operations.livedns import livedns_messages as messages
from gandi_mcp.operations.livedns.exceptions import SnapshotFailedError
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken

SNAPSHOT_ID = "snapshot_id"


class ZoneChange(EndpointOperation):
    """Replace or delete records of a zone (template method, ADR 14).

    1. ``prepare`` reads the automatic snapshots setting of the zone, then what the
       change affects (:meth:`affected`, per kind of change); a missing target is a
       Gandi error, raised before any confirmation.
    2. ``describe`` gives the effect with these counts; the confirmation offers to
       take a snapshot first, its label stating the automatic snapshots setting.
    3. ``execute`` takes the snapshot when the user chose it (``SnapshotFailedError``,
       nothing changed, if it fails), then makes the change (:meth:`change`).
    """

    def __init__(
        self,
        endpoint: Endpoint,
        domain: DomainName,
        path_values: Mapping[str, str],
        *,
        body: JsonValue = None,
        text_body: str | None = None,
        params: Mapping[str, object] | None = None,
    ) -> None:
        if endpoint.description is None:  # pragma: no cover - checked by Endpoint
            raise ValueError(f"{endpoint.name}: a zone change needs a description")
        super().__init__(endpoint, path_values, body=body, text_body=text_body)
        self._domain = domain
        self._description = endpoint.description
        self._params: dict[str, object] = {"domain": domain.unicode, **(params or {})}
        self._automatic = False

    @property
    def domain(self) -> DomainName:
        """The domain whose zone changes."""
        return self._domain

    async def prepare(
        self, client: GandiClient, environment: Environment, token: PersonalAccessToken
    ) -> None:
        details = await EndpointOperation(
            livedns_endpoints.DOMAIN_DETAILS, {"domain": self._domain.value}
        ).execute(client, environment, token)
        data = details.data
        self._automatic = isinstance(data, dict) and data.get("automatic_snapshots") is True
        self._params.update(await self.affected(client, environment, token))

    async def affected(
        self, client: GandiClient, environment: Environment, token: PersonalAccessToken
    ) -> Mapping[str, object]:
        """Read what the change affects: the counts its description names."""
        return {}

    def describe(self) -> LocalizedText:
        return LocalizedText(self._description, dict(self._params))

    def confirmation_option(self) -> ConfirmationOption:
        label: Message = (
            messages.SNAPSHOT_FIRST_AUTOMATIC if self._automatic else messages.SNAPSHOT_FIRST
        )
        return ConfirmationOption(label, default=True)

    async def execute(
        self,
        client: GandiClient,
        environment: Environment,
        token: PersonalAccessToken,
        answer: ConfirmationAnswer | None = None,
    ) -> GandiResponse:
        snapshot = None
        if answer is not None and answer.option_chosen:
            snapshot = await self._snapshot(client, environment, token)
        response = await self.change(client, environment, token, answer)
        if snapshot is None:
            return response
        return GandiResponse(
            response.status, {"result": response.data, SNAPSHOT_ID: snapshot}, location=None
        )

    async def change(
        self,
        client: GandiClient,
        environment: Environment,
        token: PersonalAccessToken,
        answer: ConfirmationAnswer | None = None,
    ) -> GandiResponse:
        """Make the change itself; the declared endpoint by default."""
        return await super().execute(client, environment, token, answer)

    async def _snapshot(
        self, client: GandiClient, environment: Environment, token: PersonalAccessToken
    ) -> JsonValue:
        try:
            response = await EndpointOperation(
                livedns_endpoints.SNAPSHOT_CREATE, {"domain": self._domain.value}, body={}
            ).execute(client, environment, token)
        except GandiError as error:
            raise SnapshotFailedError("the snapshot could not be taken") from error
        data = response.data
        return data.get("id") if isinstance(data, dict) else None
