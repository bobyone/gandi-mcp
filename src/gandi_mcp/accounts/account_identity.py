# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of the Gandi identity behind a token, displayed and never stored."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AccountIdentity:
    """Who Gandi recognizes behind a token.

    Attributes:
        username: Gandi user name. Untrusted data.
        name: Full name, when Gandi gives one. Untrusted data.
    """

    username: str
    name: str | None = None
