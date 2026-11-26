# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the system language detection."""

import sys

import pytest

from gandi_mcp.i18n import system_locale as module


def test_environment_variables_come_first(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("babel.default_locale", lambda: "de_DE")

    assert module.system_locale() == "de_DE"


def test_falls_back_to_the_platform(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("babel.default_locale", lambda: None)

    detected = module.system_locale()

    assert detected is None or isinstance(detected, str)


def test_returns_none_when_nothing_is_known(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("babel.default_locale", lambda: None)
    monkeypatch.setattr("sys.platform", "linux")
    monkeypatch.setattr("locale.getlocale", lambda: (None, None))

    assert module.system_locale() is None


@pytest.mark.skipif(sys.platform != "win32", reason="Windows user interface language")
def test_reads_the_windows_user_interface_language(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("babel.default_locale", lambda: None)
    monkeypatch.setattr("locale.getlocale", lambda: (None, None))

    assert module.system_locale() is not None
