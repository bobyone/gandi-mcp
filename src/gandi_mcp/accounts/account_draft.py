# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of an account about to be added."""

from dataclasses import dataclass

from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.environment import Environment


@dataclass(frozen=True)
class AccountDraft:
    """What the user chose for a new account, before its token is verified."""

    name: AccountName
    environment: Environment
    read_only: bool = False
