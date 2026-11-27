# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Reading the answer of a Gandi dry run (``Dry-Run: 1``)."""

from gandi_mcp.gandi.exceptions import GandiUnexpectedResponseError
from gandi_mcp.gandi.gandi_response import GandiResponse

MAX_DETAILS = 10
OK = 200


def dry_run_details(response: GandiResponse) -> tuple[str, ...] | None:
    """``None`` when Gandi accepted the dry run, else the errors it gave.

    Gandi answers ``200`` with ``{"status": "success" | "error", "errors": [...]}``;
    the details are untrusted data. Any other answer is not a successful check.

    Raises:
        GandiUnexpectedResponseError: if the answer is neither a success nor an error.
    """
    data = response.data
    status = data.get("status") if isinstance(data, dict) else None
    if response.status == OK and status == "success":
        return None
    if not isinstance(data, dict) or status != "error":
        raise GandiUnexpectedResponseError("Gandi gave no clear answer to the dry run")
    errors = data.get("errors")
    details: list[str] = []
    for error in errors if isinstance(errors, list) else []:
        if isinstance(error, dict):
            parts = (error.get("name"), error.get("description"))
            text = ": ".join(part for part in parts if isinstance(part, str) and part.strip())
            if text:
                details.append(" ".join(text.split()))
    return tuple(details[:MAX_DETAILS])
