# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Detection of the user interface language of the operating system."""

import ctypes
import locale
import sys

import babel


def system_locale() -> str | None:
    """Return the language of the operating system, or ``None`` if unknown.

    Reads ``LANGUAGE``, ``LC_ALL``, ``LC_MESSAGES`` and ``LANG`` first, then the user
    interface language on Windows, then the process locale.
    """
    detected = babel.default_locale()
    if detected:
        return detected
    if sys.platform == "win32":
        language_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        windows = locale.windows_locale.get(language_id)
        if windows:
            return windows
    current = locale.getlocale()[0]
    return current or None
