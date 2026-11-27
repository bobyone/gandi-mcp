# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of a choice the user makes together with a confirmation."""

from dataclasses import dataclass

from gandi_mcp.i18n.message import Message


@dataclass(frozen=True)
class ConfirmationOption:
    """A yes or no choice shown with a confirmation, answered outside the model (ADR 14).

    Attributes:
        label: Translatable label of the checkbox, such as "Create a snapshot first".
        default: Whether the box is checked when shown.
    """

    label: Message
    default: bool = True
