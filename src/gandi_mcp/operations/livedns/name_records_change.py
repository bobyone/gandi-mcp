# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""A destructive change of all the records of one name: replace or delete them."""

from collections.abc import Mapping

from gandi_mcp.accounts.environment import Environment
from gandi_mcp.domains.domain_name import DomainName
from gandi_mcp.gandi.gandi_client import GandiClient
from gandi_mcp.gandi.gandi_response import JsonValue
from gandi_mcp.livedns.record_name import RecordName
from gandi_mcp.operations.endpoint.endpoint import Endpoint
from gandi_mcp.operations.endpoint.endpoint_operation import EndpointOperation
from gandi_mcp.operations.livedns import livedns_endpoints
from gandi_mcp.operations.livedns.zone_change import ZoneChange
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken


class NameRecordsChange(ZoneChange):
    """Change every record of a name; its effect counts them (``count``) and, for a
    replacement, the records given (``new``)."""

    def __init__(
        self,
        endpoint: Endpoint,
        domain: DomainName,
        name: RecordName,
        *,
        body: JsonValue = None,
        new_count: int | None = None,
    ) -> None:
        super().__init__(
            endpoint,
            domain,
            {"domain": domain.value, "name": name.value},
            body=body,
            params={"name": name.value} | ({"new": new_count} if new_count is not None else {}),
        )
        self._lookup = {"domain": domain.value, "name": name.value}

    async def affected(
        self, client: GandiClient, environment: Environment, token: PersonalAccessToken
    ) -> Mapping[str, object]:
        response = await EndpointOperation(livedns_endpoints.NAME_RECORDS, self._lookup).execute(
            client, environment, token
        )
        data = response.data
        return {"count": len(data) if isinstance(data, list) else 0}
