# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of an account whose token Gandi has just accepted."""

from dataclasses import dataclass

from gandi_mcp.accounts.account_identity import AccountIdentity
from gandi_mcp.accounts.account_summary import AccountSummary


@dataclass(frozen=True)
class VerifiedAccount:
    """The account after a token change, with the identity Gandi recognized."""

    account: AccountSummary
    identity: AccountIdentity
