# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""The Gandi environments an account can target."""

from enum import StrEnum


class Environment(StrEnum):
    """Production (real effects and costs) or sandbox (tests, no effect nor cost)."""

    PRODUCTION = "production"
    SANDBOX = "sandbox"
