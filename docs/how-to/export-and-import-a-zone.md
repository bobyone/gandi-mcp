<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Export and import a zone

Save the zone of a domain, or one of its snapshots, as a zone file
(RFC 1035) on your computer, for a backup or to read long values that the
model does not get; edit it, then import it back.

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

## Import

1. Put the zone file in the work directory, for example
   `zones/example.com.zone` (an export you edited, or a file from another
   provider).
2. Ask your assistant: "import zones/example.com.zone into the zone of
   example.com". It calls `livedns_zone_import`.
3. Confirm outside the conversation: the question states how many records the
   zone has now and how many the file has; keep **Create a snapshot of the
   zone first** checked to be able to come back.

- The content of the file goes to Gandi only, never to the assistant.
- A file larger than `max_zone_file_size` (1 MiB by default, `[files]`
  section of the configuration) or not in UTF-8 is refused.
- If you change the file after the confirmation was asked, ask again: the
  confirmation is only valid for the file you saw.
- The import replaces every record of the zone with those of the file.

## When something fails

- "This file already exists in the work directory": choose another name, or
  ask to replace the file.
- "This file path is not allowed": give a name relative to the work directory.
- "The file could not be read or written": check that the work directory can
  be written by your user, that the file is UTF-8 text, or set another
  directory in the configuration.
- "This file is too large to be read": raise `max_zone_file_size`, or split
  the changes.
- "This confirmation is unknown, already used or for another operation": the
  file changed since the confirmation was asked; ask for the import again.
