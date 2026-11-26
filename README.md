<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# gandi-mcp

Manage your [Gandi](https://www.gandi.net) domains, DNS, email, certificates,
hosting and billing from your AI assistant.

`gandi-mcp` is a local MCP server (personal mode, `stdio`) with an MCP App UI,
for Claude Desktop, Claude Code and Codex, on Windows, macOS and Linux. It
covers the Gandi public API v5. Your Personal Access Token stays in your
operating system keyring and never reaches the model.

> **Status: pre-alpha.** Account management is available; Gandi features are
> delivered in batches (see [ADR 1](docs/decisions/0001-project-framing.md)).

## Documentation

- [Quick-start](docs/quick-start.md)
- [Architecture](docs/architecture.md)
- How-to guides: [add a Gandi account](docs/how-to/add-a-gandi-account.md),
  [use the Gandi sandbox](docs/how-to/use-the-sandbox.md),
  [add a Gandi operation](docs/how-to/add-an-operation.md),
  [run the checks](docs/how-to/run-the-checks.md),
  [add a language](docs/how-to/add-a-language.md),
  [configure the assistant guard](docs/how-to/configure-the-assistant-guard.md)
- [Glossary](docs/glossary.md)
- [Architecture decision records](docs/decisions/)
- Privacy: [records of processing](docs/privacy/records-of-processing.md),
  privacy policy (draft): [French, authoritative](docs/privacy/privacy-policy.fr.md),
  [English](docs/privacy/privacy-policy.md)
- [Changelog](CHANGELOG.md)

## Contributing

Contributions are welcome: read [CONTRIBUTING.md](CONTRIBUTING.md) and the
[code of conduct](CODE_OF_CONDUCT.md). Report vulnerabilities privately as
described in [SECURITY.md](SECURITY.md).

## License

`GPL-2.0-or-later`; see [LICENSE](LICENSE). The project follows the
[REUSE](https://reuse.software) specification.
