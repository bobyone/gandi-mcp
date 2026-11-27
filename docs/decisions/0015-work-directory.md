<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 15. Work directory for the user's local files

- Status: accepted
- Date: 2026-11-27
- Issue: #6

## Context

LiveDNS exports a zone or a snapshot as a zone file (RFC 1035). It also gives
configuration samples for a secondary server, and these samples hold the
secret of a TSIG key. A zone file soon exceeds the free input limit (ADR 10),
and its records are third-party data (TXT values, DKIM keys). Passing the
content through the model would withhold most of it and would expose the
conversation to injected text. Passing the TSIG secret through the model
would leak it to the LLM provider. Heavy file work belongs to the personal
mode (`mcp.md`). Writing anywhere on the computer is not acceptable either:
the model chooses the path, and it could be steered by injected text.

## Decision

- A `WorkDirectory` abstraction (`files/`) is the only place where gandi-mcp
  reads and writes the user's files. Its local implementation,
  `LocalWorkDirectory`, works in the directory set by `files.work_directory`,
  by default `<user data directory>/gandi-mcp/files`.
- Tools take a path relative to it. An absolute path, a drive letter, a `..`
  segment, a character Windows refuses in a file name, and any path that leads
  out of the directory once resolved (symbolic links included) are refused.
  The target is checked before Gandi is asked, and checked again just before
  the write.
- An existing file is replaced only when the tool call sets `overwrite`. A
  file is otherwise created exclusively, so a race cannot replace it.
- A file holding a secret (a TSIG sample) is private: mode 0600 on POSIX. On
  Windows, the permissions inherited from the user profile apply.
- The model only gets the relative path, the size and, for a zone file, the
  number of records. It never gets the content nor the absolute path, which
  holds the user's account name.
- The software never deletes a file of the work directory. Only the uninstall
  skill offers to remove the directory, after confirmation.
- Reading (zone import, sub-batch 1c-2) is bounded in size and requires UTF-8
  text.

## Alternatives considered

- **Content through the model**: no file handling, but long contents are
  withheld (ADR 10), injected text reaches the conversation and TSIG secrets
  reach the LLM provider.
- **Any absolute path chosen by the model**: flexible, but a prompt injection
  could make gandi-mcp overwrite any file the user can write.
- **The current directory of the server**: no configuration, but MCP clients
  start the server in unpredictable directories, sometimes a project the user
  works on.
- **The MCP App only**: no local file, but zone transfers configure software
  outside the App, and not every client renders MCP Apps.

## Consequences

- A new `[files]` configuration section, with `work_directory`. Sub-batch 1c-2
  adds `max_zone_file_size` for the import.
- The records of processing gain a local files processing (P3). Exported zones
  and TSIG secrets stay on the computer until the user deletes them.
- The how-tos and skills tell the user where the directory is, since the model
  does not know its absolute path.
- Exports have regression tests for each refused path, an existing file, an
  escaping symbolic link and private permissions.
