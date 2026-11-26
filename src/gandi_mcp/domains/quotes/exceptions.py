# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Exceptions of the quotes."""

from gandi_mcp.domains.exceptions import DomainError


class QuoteError(DomainError):
    """Base class of the quote errors: nothing was ordered."""


class NotAvailableError(QuoteError):
    """The domain cannot be registered (taken, reserved, forbidden...)."""

    def __init__(self, message: str, status: str) -> None:
        super().__init__(message)
        self.status = status


class NoPriceForDurationError(QuoteError):
    """Gandi gives no price for this operation and duration."""


class QuoteUnavailableError(QuoteError):
    """Gandi could not compute the quote yet: try again later."""
