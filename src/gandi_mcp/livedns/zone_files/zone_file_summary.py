# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Count the records of a zone file without interpreting their values."""

COMMENT = ";"
DIRECTIVE = "$"
CLASSES = frozenset({"IN", "CH", "HS"})


def _name_and_type(line: str, previous_name: str | None) -> tuple[str | None, str | None]:
    """The owner name and type of a resource record line (RFC 1035 master file).

    A line starting with a blank repeats the previous owner name. The type is the
    first field after the name that is neither a TTL nor a class.
    """
    fields = line.split()
    if line[:1].isspace():
        name, rest = previous_name, fields
    else:
        name, rest = fields[0], fields[1:]
    for field in rest:
        if field.isdigit() or field.upper() in CLASSES:
            continue
        return name, field.upper()
    return name, None


def record_count(zone_file: str) -> int:
    """Number of records of a zone file: distinct name and type pairs (RRsets).

    Blank lines, comments and directives (``$ORIGIN``, ``$TTL``) are skipped; the
    values of one name and type count once, whether on one or several lines; a
    record spread over several lines between parentheses counts once. The count is
    shown to the model instead of the content, which stays untrusted data.
    """
    records: set[tuple[str | None, str]] = set()
    previous_name: str | None = None
    depth = 0
    for line in zone_file.splitlines():
        content = line.split(COMMENT, 1)[0]
        if depth == 0 and content.strip() and not content.strip().startswith(DIRECTIVE):
            name, record_type = _name_and_type(content, previous_name)
            previous_name = name
            if record_type is not None:
                records.add((name.lower() if name else name, record_type))
        depth = max(0, depth + content.count("(") - content.count(")"))
    return len(records)
