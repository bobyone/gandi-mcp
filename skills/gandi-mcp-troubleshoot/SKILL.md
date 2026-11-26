---
name: gandi-mcp-troubleshoot
description: Diagnose gandi-mcp problems (server not starting or not connected, configuration errors, missing tools) and read its logs. Use when gandi-mcp fails, disconnects, or behaves unexpectedly.
---

# Troubleshoot gandi-mcp

1. Check the version:
   `uvx --from git+https://github.com/bobyone/gandi-mcp gandi-mcp --version`.
   A failure here points to `uv` or the network; reinstall with the
   `gandi-mcp-install` skill.
2. Exit status 2 at start means a configuration error: the log line names the
   invalid key. Ask the user to compare their file with `config.example.toml`;
   never open their `config.toml` yourself.
3. Logs go to stderr, which the client captures:
   - Claude Code: `/mcp` shows the server status; `claude --debug` shows its
     output;
   - Claude Desktop: the MCP log files of the application (Settings,
     Developer);
   - Codex: the client's session logs.
   For more detail, ask the user to set `logging.level = "DEBUG"` in their
   configuration and restart the client.
4. Logs contain no token nor personal data by design. Still check a log line
   before quoting it in an issue.
5. If the problem persists, use the `gandi-mcp-report-issue` skill.
