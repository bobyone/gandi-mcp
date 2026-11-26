# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the packaged MCP App HTML."""

from pathlib import Path

import pytest

from gandi_mcp.protocol.app.app_resource import (
    APP_FILE,
    AppResourceMissingError,
    load_app_html,
)


def test_the_built_app_is_shipped() -> None:
    html = load_app_html()

    assert html.lstrip().lower().startswith("<!doctype html>")
    assert "<script" in html
    assert 'src="http' not in html
    assert (APP_FILE.parent / "THIRD_PARTY_NOTICES.md").is_file()


def test_a_missing_build_is_explained(tmp_path: Path) -> None:
    with pytest.raises(AppResourceMissingError, match=r"not built"):
        load_app_html(tmp_path / "app.html")
