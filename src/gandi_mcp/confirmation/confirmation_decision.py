# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of the outcome of a confirmation request."""

from dataclasses import dataclass, field

from gandi_mcp.secrets.secret_value import SecretValue


@dataclass(frozen=True)
class ConfirmationDecision:
    """Either accepted now, or pending on a local page.

    A refused or expired confirmation is an exception, never a decision.

    Attributes:
        accepted: Whether the operation may run now.
        confirmation_id: Identifier of the pending confirmation, to give back once the
            user has answered on the page; ``None`` when accepted.
        secret: The secret typed with an accepted confirmation, when one was asked.
    """

    accepted: bool
    confirmation_id: str | None = None
    secret: SecretValue | None = field(default=None, repr=False)

    @classmethod
    def accept(cls, secret: SecretValue | None = None) -> "ConfirmationDecision":
        """The operation may run now, with the secret typed by the user if any."""
        return cls(accepted=True, secret=secret)

    @classmethod
    def pending(cls, confirmation_id: str) -> "ConfirmationDecision":
        """The user answers on a local page; call again with this identifier."""
        return cls(accepted=False, confirmation_id=confirmation_id)
