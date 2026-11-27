# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of what the user gave with an accepted confirmation."""

from dataclasses import dataclass, field

from gandi_mcp.secrets.secret_value import SecretValue


@dataclass(frozen=True)
class ConfirmationAnswer:
    """Passed to :meth:`Operation.execute` once the user accepted (ADR 14).

    Attributes:
        secret: The secret typed with the confirmation, when one was asked (ADR 11).
        option_chosen: Whether the user checked the confirmation option, when one
            was offered.
    """

    secret: SecretValue | None = field(default=None, repr=False)
    option_chosen: bool = False
