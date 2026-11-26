# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Reading the answer of a Gandi dry run (``Dry-Run: 1``)."""

from gandi_mcp.gandi.gandi_response import GandiResponse

MAX_DETAILS = 10


def dry_run_details(response: GandiResponse) -> tuple[str, ...] | None:
    """The errors of a failed dry run, or ``None`` when Gandi accepted it.

    Gandi answers ``{"status": "success" | "error", "errors": [{name, description}]}``;
    the details are untrusted data.
    """
    data = response.data
    if not isinstance(data, dict) or data.get("status") != "error":
        return None
    errors = data.get("errors")
    details: list[str] = []
    for error in errors if isinstance(errors, list) else []:
        if isinstance(error, dict):
            parts = (error.get("name"), error.get("description"))
            text = ": ".join(part for part in parts if isinstance(part, str) and part.strip())
            if text:
                details.append(" ".join(text.split()))
    return tuple(details[:MAX_DETAILS])
