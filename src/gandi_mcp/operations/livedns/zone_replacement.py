# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""A destructive change of the whole zone: replace it (records or zone file) or empty it."""

from collections.abc import Mapping

from gandi_mcp.accounts.environment import Environment
from gandi_mcp.domains.domain_name import DomainName
from gandi_mcp.gandi.gandi_client import GandiClient
from gandi_mcp.gandi.gandi_response import JsonValue
from gandi_mcp.operations.endpoint.endpoint import Endpoint
from gandi_mcp.operations.endpoint.endpoint_operation import EndpointOperation
from gandi_mcp.operations.livedns import livedns_endpoints
from gandi_mcp.operations.livedns.zone_change import ZoneChange
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken

# Records given to one replacement at most; a larger zone goes through a zone file.
MAX_REPLACED_RECORDS = 1000


class ZoneReplacement(ZoneChange):
    """Change all the records of a zone; its effect counts them (``count``, read from
    the total of the record list) and the records given (``new``)."""

    def __init__(
        self,
        endpoint: Endpoint,
        domain: DomainName,
        *,
        body: JsonValue = None,
        text_body: str | None = None,
        new_count: int | None = None,
        params: Mapping[str, object] | None = None,
    ) -> None:
        extra = dict(params or {})
        if new_count is not None:
            extra["new"] = new_count
        super().__init__(
            endpoint,
            domain,
            {"domain": domain.value},
            body=body,
            text_body=text_body,
            params=extra,
        )

    async def affected(
        self, client: GandiClient, environment: Environment, token: PersonalAccessToken
    ) -> Mapping[str, object]:
        response = await EndpointOperation(
            livedns_endpoints.RECORD_LIST,
            {"domain": self.domain.value},
            {"page": 1, "per_page": 1},
        ).execute(client, environment, token)
        if response.total_count is not None:
            return {"count": response.total_count}
        return {"count": len(response.data) if isinstance(response.data, list) else 0}
