# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of a confirmation waiting for the user's answer on a local page."""

from dataclasses import dataclass, field
from enum import StrEnum

from gandi_mcp.confirmation.confirmation_request import ConfirmationRequest
from gandi_mcp.secrets.secret_value import SecretValue


class PendingState(StrEnum):
    """States of a pending confirmation; accepted and refused are final."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REFUSED = "refused"


@dataclass(frozen=True)
class PendingConfirmation:
    """A confirmation request, its identifier, deadline, state and typed secret."""

    confirmation_id: str
    request: ConfirmationRequest
    deadline: float
    state: PendingState = PendingState.PENDING
    secret: SecretValue | None = field(default=None, repr=False)
