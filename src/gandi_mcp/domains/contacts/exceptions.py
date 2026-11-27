# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Exceptions of the domain contacts."""

from gandi_mcp.domains.exceptions import DomainError


class InvalidContactError(DomainError):
    """A contact field is missing, too long or badly formed."""
