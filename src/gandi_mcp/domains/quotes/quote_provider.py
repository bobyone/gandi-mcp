# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Abstraction of the pricing of billable domain operations."""

from abc import ABC, abstractmethod

from gandi_mcp.accounts.environment import Environment
from gandi_mcp.domains.quotes.quote import Quote
from gandi_mcp.domains.quotes.quote_request import QuoteRequest
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken


class QuoteProvider(ABC):
    """Price an operation for the user behind a token (strategy)."""

    @abstractmethod
    async def quote(
        self, environment: Environment, token: PersonalAccessToken, request: QuoteRequest
    ) -> Quote:
        """Return the current price of the requested operation.

        Raises:
            NotAvailableError: if a domain to register is not available.
            NoPriceForDurationError: if no price exists for this duration.
            QuoteUnavailableError: if the price cannot be computed now.
            GandiError: if Gandi refuses or cannot be reached.
        """
