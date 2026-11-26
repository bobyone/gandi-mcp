# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the operation categories."""

from gandi_mcp.operations.operation_category import OperationCategory


def test_rules_per_category() -> None:
    rules = {
        category: (category.is_write, category.needs_confirmation) for category in OperationCategory
    }

    assert rules == {
        OperationCategory.READ: (False, False),
        OperationCategory.WRITE: (True, False),
        OperationCategory.DESTRUCTIVE: (True, True),
        OperationCategory.BILLABLE: (True, True),
    }
