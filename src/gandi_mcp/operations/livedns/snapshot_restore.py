# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Restore a snapshot: replace the records of the zone with those of the snapshot."""

from collections.abc import Mapping

from gandi_mcp.accounts.environment import Environment
from gandi_mcp.domains.domain_name import DomainName
from gandi_mcp.gandi.exceptions import GandiUnexpectedResponseError
from gandi_mcp.gandi.gandi_client import GandiClient
from gandi_mcp.gandi.gandi_response import GandiResponse, JsonValue
from gandi_mcp.livedns.identifiers import SnapshotId
from gandi_mcp.operations.confirmation_answer import ConfirmationAnswer
from gandi_mcp.operations.endpoint.endpoint_operation import EndpointOperation
from gandi_mcp.operations.livedns import livedns_endpoints
from gandi_mcp.operations.livedns.zone_replacement import ZoneReplacement
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken


class SnapshotRestore(ZoneReplacement):
    """Read a snapshot, then replace the zone with its records (no restore endpoint).

    ``prepare`` also reads the snapshot, for its name and number of records; the
    change reads it again, so that a resumed confirmation sends the snapshot content
    as it is at that time. The confirmation is bound to the snapshot identifier.
    """

    def __init__(self, domain: DomainName, snapshot: SnapshotId) -> None:
        super().__init__(
            livedns_endpoints.SNAPSHOT_RESTORE,
            domain,
            body={"snapshot": snapshot.value},
            params={"snapshot": snapshot.value},
        )
        self._snapshot_id = snapshot

    async def affected(
        self, client: GandiClient, environment: Environment, token: PersonalAccessToken
    ) -> Mapping[str, object]:
        counts = dict(await super().affected(client, environment, token))
        snapshot = await self._read(client, environment, token)
        name = snapshot.get("name")
        counts["snapshot"] = name if isinstance(name, str) and name else self._snapshot_id.value
        counts["new"] = len(self._records(snapshot))
        return counts

    async def change(
        self,
        client: GandiClient,
        environment: Environment,
        token: PersonalAccessToken,
        answer: ConfirmationAnswer | None = None,
    ) -> GandiResponse:
        records = self._records(await self._read(client, environment, token))
        return await client.request(
            environment,
            token,
            "PUT",
            ("livedns", "domains", self.domain.value, "records"),
            body={"items": records},
        )

    async def _read(
        self, client: GandiClient, environment: Environment, token: PersonalAccessToken
    ) -> dict[str, JsonValue]:
        response = await EndpointOperation(
            livedns_endpoints.SNAPSHOT_DETAILS,
            {"domain": self.domain.value, "snapshot": self._snapshot_id.value},
        ).execute(client, environment, token)
        if not isinstance(response.data, dict):
            raise GandiUnexpectedResponseError("Gandi returned no snapshot")
        return response.data

    @staticmethod
    def _records(snapshot: Mapping[str, JsonValue]) -> list[JsonValue]:
        records = snapshot.get("zone_data")
        if not isinstance(records, list):
            raise GandiUnexpectedResponseError("the snapshot has no records")
        return records
