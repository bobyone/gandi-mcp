# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Categories of operations, which decide the read-only and confirmation rules."""

from enum import StrEnum


class OperationCategory(StrEnum):
    """Read, write, destructive or billable; destructive and billable are writes."""

    READ = "read"
    WRITE = "write"
    DESTRUCTIVE = "destructive"
    BILLABLE = "billable"

    @property
    def is_write(self) -> bool:
        """Whether a read-only account refuses the operation."""
        return self is not OperationCategory.READ

    @property
    def needs_confirmation(self) -> bool:
        """Whether the user must confirm the operation first."""
        return self in {OperationCategory.DESTRUCTIVE, OperationCategory.BILLABLE}
