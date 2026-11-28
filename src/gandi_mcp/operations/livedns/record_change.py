# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""A destructive change of one record: replace it, remove values, or delete it."""

from collections.abc import Mapping, Sequence

from gandi_mcp.accounts.environment import Environment
from gandi_mcp.domains.domain_name import DomainName
from gandi_mcp.gandi.gandi_client import GandiClient
from gandi_mcp.gandi.gandi_response import JsonValue
from gandi_mcp.livedns.record_name import RecordName
from gandi_mcp.livedns.record_type import RecordType
from gandi_mcp.livedns.record_value import RecordValue
from gandi_mcp.operations.endpoint.endpoint import Endpoint
from gandi_mcp.operations.endpoint.endpoint_operation import EndpointOperation
from gandi_mcp.operations.livedns import livedns_endpoints
from gandi_mcp.operations.livedns.zone_change import ZoneChange
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken


class RecordChange(ZoneChange):
    """Change the record of a name and type.

    Its effect counts the current values of the record (``count``), and, for a
    replacement, the new ones (``new``); for a removal, ``count`` is the number of
    current values removed and ``left`` the number kept.
    """

    def __init__(
        self,
        endpoint: Endpoint,
        domain: DomainName,
        name: RecordName,
        record_type: RecordType,
        *,
        body: JsonValue = None,
        new_values: Sequence[RecordValue] | None = None,
        removed_values: Sequence[RecordValue] | None = None,
    ) -> None:
        super().__init__(
            endpoint,
            domain,
            {"domain": domain.value, "name": name.value, "type": record_type.value},
            body=body,
            params={"name": name.value, "type": record_type.value},
        )
        self._lookup = {"domain": domain.value, "name": name.value, "type": record_type.value}
        self._new = len(new_values) if new_values is not None else None
        self._removed = {value.value for value in removed_values or ()}
        self._removal = removed_values is not None

    async def affected(
        self, client: GandiClient, environment: Environment, token: PersonalAccessToken
    ) -> Mapping[str, object]:
        response = await EndpointOperation(livedns_endpoints.RECORD, self._lookup).execute(
            client, environment, token
        )
        data = response.data
        raw = data.get("rrset_values") if isinstance(data, dict) else None
        current = (
            [value for value in raw if isinstance(value, str)] if isinstance(raw, list) else []
        )
        if self._removal:
            removed = sum(1 for value in current if value in self._removed)
            return {"count": removed, "left": len(current) - removed}
        counts: dict[str, object] = {"count": len(current)}
        if self._new is not None:
            counts["new"] = self._new
        return counts
