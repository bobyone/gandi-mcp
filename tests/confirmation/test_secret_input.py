# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the secret asked with a confirmation."""

import pytest

from gandi_mcp.confirmation.secret_input import SecretInput
from gandi_mcp.i18n.message import Message
from gandi_mcp.secrets.secret_value import MAX_SECRET_LENGTH


def test_bounds() -> None:
    assert SecretInput(Message("Code")).max_length == MAX_SECRET_LENGTH
    for wrong in (0, MAX_SECRET_LENGTH + 1):
        with pytest.raises(ValueError, match="max_length"):
            SecretInput(Message("Code"), wrong)
