# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""The billable processes Gandi prices for a domain."""

from enum import StrEnum


class DomainProcess(StrEnum):
    """Registration, renewal, transfer in and restore."""

    CREATE = "create"
    RENEW = "renew"
    TRANSFER = "transfer"
    RESTORE = "restore"
