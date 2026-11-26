# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Exceptions of the preferences notion."""


class PreferencesError(Exception):
    """Base class of the preferences errors."""


class CorruptPreferencesError(PreferencesError):
    """Raised when the preferences cannot be understood; they are never overwritten."""


class PreferencesUnavailableError(PreferencesError):
    """Raised when the preferences cannot be read or written (permissions, disk)."""
