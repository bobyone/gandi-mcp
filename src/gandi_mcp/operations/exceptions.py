# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Exceptions of the orders (billable operations)."""

from gandi_mcp.gandi.exceptions import GandiValidationError


class OrderError(Exception):
    """Base class of the order errors: nothing was bought."""


class DryRunRejectedError(OrderError, GandiValidationError):
    """Gandi refused the order when checking it (``Dry-Run``); details are untrusted."""


class PriceChangedError(OrderError):
    """The price changed between the confirmation and the order."""
