# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object identifying an account as the user saw it, whatever its name."""

from dataclasses import dataclass

from gandi_mcp.accounts.environment import Environment


@dataclass(frozen=True)
class AccountReference:
    """The stable identity of an account and its environment.

    A confirmation or a token entry page is bound to it: a renamed account keeps it,
    while an account replaced under the same name, or moved to another environment,
    no longer matches.

    Attributes:
        secret_key: Opaque key of the account, set when it is added.
        environment: Environment of the account when the user was asked.
    """

    secret_key: str
    environment: Environment

    def fingerprint(self) -> str:
        """Text form, used in confirmation subjects."""
        return f"{self.secret_key}:{self.environment.value}"
