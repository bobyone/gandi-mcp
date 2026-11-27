# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of a secret the user types together with a confirmation."""

from dataclasses import dataclass

from gandi_mcp.i18n.message import Message
from gandi_mcp.secrets.secret_value import MAX_SECRET_LENGTH


@dataclass(frozen=True)
class SecretInput:
    """A secret asked with a confirmation, outside the model (ADR 11).

    Attributes:
        label: Translatable label of the field, such as "Authorization code".
        max_length: Longest accepted value.
    """

    label: Message
    max_length: int = MAX_SECRET_LENGTH

    def __post_init__(self) -> None:
        if not 1 <= self.max_length <= MAX_SECRET_LENGTH:
            raise ValueError(f"max_length is between 1 and {MAX_SECRET_LENGTH}")
