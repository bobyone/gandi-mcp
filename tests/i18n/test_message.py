# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the message markers."""

from gandi_mcp.i18n.message import N_, Message, ngettext


def test_markers_build_messages() -> None:
    assert N_("Hi") == Message("Hi")
    assert not N_("Hi").is_plural
    assert ngettext("{count} file", "{count} files").is_plural
