# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Exceptions of the token entry notion."""


class TokenEntryError(Exception):
    """Base class of the token entry errors."""


class SessionExpiredError(TokenEntryError):
    """The session deadline has passed."""


class SessionUsedError(TokenEntryError):
    """The session is unknown or already used: a session accepts one submission."""


class TokenEntryUnavailableError(TokenEntryError):
    """The token entry page could not be shown to the user."""
