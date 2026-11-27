# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Read the configuration sample of a TSIG key together with its secret."""

from collections.abc import Mapping

from gandi_mcp.accounts.environment import Environment
from gandi_mcp.gandi.exceptions import GandiUnexpectedResponseError
from gandi_mcp.gandi.gandi_client import GandiClient
from gandi_mcp.gandi.gandi_response import GandiResponse, JsonValue
from gandi_mcp.i18n.localized_text import LocalizedText
from gandi_mcp.i18n.message import Message
from gandi_mcp.livedns.identifiers import TsigKeyId
from gandi_mcp.livedns.tsig_software import TsigSoftware
from gandi_mcp.operations.endpoint.endpoint_operation import EndpointOperation
from gandi_mcp.operations.livedns import livedns_endpoints
from gandi_mcp.operations.operation import Operation
from gandi_mcp.operations.operation_category import OperationCategory
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from gandi_mcp.secrets.secret_value import SecretValue

CONFIGURATION = "configuration"
SECRET = "secret"  # noqa: S105 - field name, not a secret


class TsigConfiguration(Operation):
    """Read a TSIG key, then its configuration sample for a server software.

    The result is ``{"key_id", "software", "configuration", "secret"}``: the
    ``secret`` field lets the secret field filter hide the secret wherever the sample
    repeats it, before the model sees it; the full sample only goes to a file of the
    work directory.
    """

    def __init__(
        self, key: TsigKeyId, software: TsigSoftware, sharing_id: str | None = None
    ) -> None:
        query = {"sharing_id": sharing_id}
        self._key = key
        self._software = software
        self._details = EndpointOperation(
            livedns_endpoints.TSIG_KEY_DETAILS, {"key": key.value}, query
        )
        self._sample = EndpointOperation(
            livedns_endpoints.TSIG_CONFIG,
            {"key": key.value, "software": software.value},
            query,
        )

    @property
    def name(self) -> str:
        return livedns_endpoints.TSIG_CONFIG.name

    @property
    def category(self) -> OperationCategory:
        return OperationCategory.READ

    def parameters(self) -> Mapping[str, JsonValue]:
        return self._sample.parameters()

    def describe(self) -> LocalizedText:
        return LocalizedText(Message(self.name))

    async def execute(
        self,
        client: GandiClient,
        environment: Environment,
        token: PersonalAccessToken,
        secret: SecretValue | None = None,
    ) -> GandiResponse:
        details = await self._details.execute(client, environment, token)
        sample = await self._sample.execute(client, environment, token)
        key_secret = details.data.get(SECRET) if isinstance(details.data, dict) else None
        if not isinstance(sample.data, str):
            raise GandiUnexpectedResponseError("Gandi returned no configuration sample")
        return GandiResponse(
            sample.status,
            {
                "key_id": self._key.value,
                "software": self._software.value,
                CONFIGURATION: sample.data,
                SECRET: key_secret if isinstance(key_secret, str) else None,
            },
        )
