# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Keeping a secret typed by the user out of what Gandi answers (ADR 11)."""

from gandi_mcp.gandi.exceptions import GandiError
from gandi_mcp.gandi.gandi_response import JsonValue
from gandi_mcp.secrets.secret_value import SecretValue

HIDDEN = "hidden"


def scrubbed(data: JsonValue, secret: SecretValue) -> JsonValue:
    """A copy of ``data`` with no keys or text values containing the secret."""
    value = secret.reveal()
    if isinstance(data, list):
        return [scrubbed(item, secret) for item in data]
    if isinstance(data, dict):
        return {key: scrubbed(item, secret) for key, item in data.items() if value not in key}
    if isinstance(data, str) and value in data:
        return HIDDEN
    return data


def without_details(error: GandiError) -> GandiError:
    """The same error without Gandi's free-text details, which may echo the secret."""
    error.details = ()
    return error
