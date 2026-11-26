# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Organizations listed by the Gandi Organization API."""

from gandi_mcp.accounts.environment import Environment
from gandi_mcp.accounts.exceptions import InvalidOrganizationIdError
from gandi_mcp.accounts.organization import Organization
from gandi_mcp.accounts.organization_directory import OrganizationDirectory
from gandi_mcp.accounts.organization_id import OrganizationId
from gandi_mcp.gandi.exceptions import GandiUnexpectedResponseError
from gandi_mcp.gandi.gandi_client import GandiClient
from gandi_mcp.gandi.gandi_response import JsonValue
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken

ORGANIZATIONS_PATH = ("organization", "organizations")
MAX_FIELD_LENGTH = 100
MAX_ORGANIZATIONS = 500


def _text(value: JsonValue) -> str:
    return " ".join(value.split())[:MAX_FIELD_LENGTH] if isinstance(value, str) else ""


def _organization(entry: JsonValue) -> Organization | None:
    if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
        return None
    try:
        identifier = OrganizationId(str(entry["id"]))
    except InvalidOrganizationIdError:
        return None
    return Organization(identifier, _text(entry.get("name")), _text(entry.get("type")))


class GandiOrganizationDirectory(OrganizationDirectory):
    """Call ``GET /organization/organizations``; keep only the id, name and type.

    The other fields (names, addresses, emails of the organization contacts) are
    never read.
    """

    def __init__(self, client: GandiClient) -> None:
        self._client = client

    async def organizations(
        self, environment: Environment, token: PersonalAccessToken
    ) -> tuple[Organization, ...]:
        response = await self._client.request(
            environment, token, "GET", ORGANIZATIONS_PATH, query={"per_page": MAX_ORGANIZATIONS}
        )
        if not isinstance(response.data, list):
            raise GandiUnexpectedResponseError("Gandi returned no list of organizations")
        found = (_organization(entry) for entry in response.data)
        return tuple(organization for organization in found if organization is not None)
