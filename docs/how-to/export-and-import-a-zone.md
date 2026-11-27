<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Export a zone to a file

Save the zone of a domain, or one of its snapshots, as a zone file
(RFC 1035) on your computer, for a backup or to read long values that the
model does not get.

> The import of a zone file comes with the zone changes, in the next
> sub-batch of issue #6.

## Where the files go

gandi-mcp only writes in its **work directory** (ADR 15):

| System | Default work directory |
| --- | --- |
| Windows | `%LOCALAPPDATA%\gandi-mcp\files` |
| macOS | `~/Library/Application Support/gandi-mcp/files` |
| Linux | `~/.local/share/gandi-mcp/files` (or `$XDG_DATA_HOME/gandi-mcp/files`) |

To use another directory, set `work_directory` in the `[files]` section of
your configuration file (see `gandi-mcp.example.toml` and the
[quick-start](../quick-start.md)), then restart your client.

File names are relative to this directory. Subdirectories are allowed, for
example `zones/example.com.zone`. An absolute path, a drive letter or `..` is
refused, and so is any path leading out of the directory through a symbolic
link.

## Export

Ask your assistant, for example "export the zone of example.com to
zones/example.com.zone". It calls `livedns_zone_export`, or
`livedns_snapshot_export` for a snapshot (take its identifier from
`livedns_snapshots`).

- The assistant only learns the file name, its size and its number of
  records. The content stays in the file and never reaches the model.
- An existing file is kept: the export fails unless you ask the assistant to
  replace it.
- The software never deletes these files: remove them yourself when you no
  longer need them. A zone may hold personal data (an email address in a TXT
  record).

## When something fails

- "This file already exists in the work directory": choose another name, or
  ask to replace the file.
- "This file path is not allowed": give a name relative to the work directory.
- "The file could not be read or written": check that the work directory can
  be written by your user, or set another one in the configuration.
