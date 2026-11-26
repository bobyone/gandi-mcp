# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Consistency checks of the plugin manifests with the package metadata."""

import json
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def load_json(relative: str) -> Any:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def project_version() -> str:
    with (ROOT / "pyproject.toml").open("rb") as stream:
        return str(tomllib.load(stream)["project"]["version"])


def test_portable_manifest_carries_the_software_version() -> None:
    assert load_json("plugin.json")["version"] == project_version()


def test_claude_manifests_have_no_version() -> None:
    marketplace = load_json(".claude-plugin/marketplace.json")

    assert "version" not in load_json(".claude-plugin/plugin.json")
    assert all("version" not in plugin for plugin in marketplace["plugins"])


def test_manifests_share_the_plugin_name_and_server() -> None:
    claude = load_json(".claude-plugin/plugin.json")
    portable = load_json("plugin.json")
    codex = load_json(".agents/plugins/marketplace.json")

    assert claude["name"] == portable["name"] == codex["plugins"][0]["name"] == "gandi-mcp"
    assert claude["mcpServers"] == portable["mcpServers"]
    assert codex["plugins"][0]["source"]["path"] == "./"


def test_every_skill_has_a_description() -> None:
    skills = sorted(ROOT.glob("skills/*/SKILL.md")) + sorted(ROOT.glob(".*/skills/*/SKILL.md"))

    assert skills
    for path in skills:
        header = path.read_text(encoding="utf-8").split("---")[1]
        assert f"name: {path.parent.name}" in header
        assert "description:" in header
