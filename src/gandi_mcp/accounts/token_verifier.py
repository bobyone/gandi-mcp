# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Abstraction of the verification of a token before it is kept."""

from abc import ABC, abstractmethod

from gandi_mcp.accounts.account_identity import AccountIdentity
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken


class TokenVerifier(ABC):
    """Check that Gandi accepts a token in an environment."""

    @abstractmethod
    async def verify(self, environment: Environment, token: PersonalAccessToken) -> AccountIdentity:
        """Return the identity Gandi recognizes behind the token.

        Raises:
            TokenRejectedError: if Gandi refuses the token in this environment.
            GandiError: if Gandi cannot be reached or answers unexpectedly.
        """
