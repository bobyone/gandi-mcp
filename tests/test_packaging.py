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


PORTABLE_PLUGIN_KEYS = {
    "$schema",
    "name",
    "version",
    "description",
    "author",
    "homepage",
    "repository",
    "license",
    "keywords",
    "extensions",
}
STDIO_SERVER_KEYS = {"type", "command", "args", "env", "cwd"}


def test_portable_manifest_follows_agent_plugins_1_0() -> None:
    manifest = load_json("plugin.json")

    assert manifest["$schema"] == "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
    assert set(manifest) <= PORTABLE_PLUGIN_KEYS
    assert "mcpServers" not in manifest


def test_portable_mcp_configuration_declares_a_stdio_server() -> None:
    configuration = load_json("mcp.json")

    assert configuration["$schema"] == "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"
    assert set(configuration) == {"$schema", "mcpServers"}
    server = configuration["mcpServers"]["gandi"]
    assert server["type"] == "stdio"
    assert set(server) <= STDIO_SERVER_KEYS


def test_codex_marketplace_entry() -> None:
    entry = load_json(".agents/plugins/marketplace.json")["plugins"][0]

    assert entry["source"] == {"source": "local", "path": "./"}
    assert {"installation", "authentication"} <= set(entry["policy"])
    assert entry["category"]


def test_manifests_share_the_plugin_name_and_server() -> None:
    claude = load_json(".claude-plugin/plugin.json")
    portable = load_json("plugin.json")
    codex = load_json(".agents/plugins/marketplace.json")
    server = load_json("mcp.json")["mcpServers"]["gandi"]

    assert claude["name"] == portable["name"] == codex["plugins"][0]["name"] == "gandi-mcp"
    claude_server = claude["mcpServers"]["gandi"]
    assert (claude_server["command"], claude_server["args"]) == (server["command"], server["args"])


def test_every_skill_has_a_description() -> None:
    skills = sorted(ROOT.glob("skills/*/SKILL.md")) + sorted(ROOT.glob(".*/skills/*/SKILL.md"))

    assert skills
    for path in skills:
        header = path.read_text(encoding="utf-8").split("---")[1]
        assert f"name: {path.parent.name}" in header
        assert "description:" in header
