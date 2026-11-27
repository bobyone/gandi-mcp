# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Count the records of a zone file without interpreting it."""

COMMENT = ";"
DIRECTIVE = "$"


def record_count(zone_file: str) -> int:
    """Number of records of a zone file (RFC 1035 master file).

    Blank lines, comments and directives (``$ORIGIN``, ``$TTL``) are not records; a
    record spread over several lines between parentheses counts once. The count is
    shown to the model instead of the content, which stays untrusted data.
    """
    count = 0
    depth = 0
    for line in zone_file.splitlines():
        content = line.split(COMMENT, 1)[0]
        stripped = content.strip()
        if depth == 0 and stripped and not stripped.startswith(DIRECTIVE):
            count += 1
        depth = max(0, depth + content.count("(") - content.count(")"))
    return count
