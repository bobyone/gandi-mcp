# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Abstraction of the list of the organizations a token can use."""

from abc import ABC, abstractmethod

from gandi_mcp.accounts.environment import Environment
from gandi_mcp.accounts.organization import Organization
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken


class OrganizationDirectory(ABC):
    """List the organizations of the user behind a token (strategy)."""

    @abstractmethod
    async def organizations(
        self, environment: Environment, token: PersonalAccessToken
    ) -> tuple[Organization, ...]:
        """Return the organizations the token can use, in the order Gandi gives them.

        Raises:
            GandiError: if Gandi refuses or cannot be reached.
        """
