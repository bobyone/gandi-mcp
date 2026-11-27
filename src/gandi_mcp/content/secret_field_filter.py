# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Keep the secrets returned by Gandi (TSIG keys) away from the model."""

from gandi_mcp.content.disclosure import Disclosure
from gandi_mcp.content.result_filter import ResultFilter
from gandi_mcp.gandi.gandi_response import JsonValue

SECRET_FIELD = "secret"  # noqa: S105 - field name, not a secret
HIDDEN = "hidden"
HIDDEN_IN_TEXT = "<hidden>"


def _secrets(data: JsonValue) -> set[str]:
    """The non-empty text values of the ``secret`` fields, at any depth."""
    if isinstance(data, list):
        return {secret for item in data for secret in _secrets(item)}
    if isinstance(data, dict):
        found = {secret for value in data.values() for secret in _secrets(value)}
        value = data.get(SECRET_FIELD)
        if isinstance(value, str) and value:
            found.add(value)
        return found
    return set()


class SecretFieldFilter(ResultFilter):
    """Hide every ``secret`` field, and that secret wherever it is repeated.

    At any depth, the value of a ``secret`` field becomes ``"hidden"``, and any text
    of the same result containing one of these secrets (a configuration sample) has
    it replaced by ``<hidden>``. Nothing can be disclosed on request: a secret is only
    ever shown outside the conversation (MCP App, file of the work directory).
    """

    def filter(self, data: JsonValue, disclosure: Disclosure) -> JsonValue:
        """Hide the secrets; ``disclosure`` is ignored."""
        secrets = sorted(_secrets(data), key=len, reverse=True)
        return self._apply(data, secrets)

    def _apply(self, data: JsonValue, secrets: list[str]) -> JsonValue:
        if isinstance(data, list):
            return [self._apply(item, secrets) for item in data]
        if isinstance(data, dict):
            return {
                key: (HIDDEN if value else value)
                if key == SECRET_FIELD
                else self._apply(value, secrets)
                for key, value in data.items()
            }
        if isinstance(data, str):
            for secret in secrets:
                data = data.replace(secret, HIDDEN_IN_TEXT)
        return data
