# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Exceptions of the internationalization notion."""


class TranslationError(Exception):
    """Raised when a message cannot be rendered (missing parameter, broken catalog)."""
