# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of what a submitted token is for."""

from dataclasses import dataclass
from enum import StrEnum

from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.environment import Environment


class TokenPurpose(StrEnum):
    """Add an account, replace its token, or move it to another environment."""

    ADD = "add"
    REPLACE = "replace"
    CHANGE_ENVIRONMENT = "change_environment"


@dataclass(frozen=True)
class TokenEntryTarget:
    """The account a token entry session is for.

    Attributes:
        purpose: What the token is used for.
        name: Account name (new for ``ADD``, existing otherwise).
        environment: Environment the token must be valid in.
        read_only: Read-only flag of a new account (``ADD`` only).
    """

    purpose: TokenPurpose
    name: AccountName
    environment: Environment
    read_only: bool = False
