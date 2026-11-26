# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Exceptions of the confirmation notion."""


class ConfirmationError(Exception):
    """Base class of the confirmation errors; the operation had no effect."""


class ConfirmationRefusedError(ConfirmationError):
    """The user refused or cancelled the confirmation."""


class ConfirmationExpiredError(ConfirmationError):
    """The confirmation was not given in time."""


class ConfirmationUnavailableError(ConfirmationError):
    """No channel could reach the user (no elicitation, no interface, no browser)."""


class ConfirmationMismatchError(ConfirmationError):
    """The confirmation identifier is unknown, used, or for another operation."""
