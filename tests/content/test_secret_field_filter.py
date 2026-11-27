# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the hiding of the secrets returned by Gandi."""

import json

from gandi_mcp.content.disclosure import Disclosure
from gandi_mcp.content.secret_field_filter import HIDDEN, HIDDEN_IN_TEXT, SecretFieldFilter
from gandi_mcp.gandi.gandi_response import JsonValue

SECRET = "c2VjcmV0LXRzaWcta2V5LXZhbHVl"


def test_secret_fields_are_hidden_at_any_depth() -> None:
    data: JsonValue = [
        {"id": "k1", "key_name": "transfer", "secret": SECRET},
        {"nested": {"secret": "other-secret"}},
    ]

    filtered = SecretFieldFilter().filter(data, Disclosure())

    assert filtered == [
        {"id": "k1", "key_name": "transfer", "secret": HIDDEN},
        {"nested": {"secret": HIDDEN}},
    ]
    assert SECRET not in json.dumps(filtered)


def test_a_secret_repeated_in_a_text_is_hidden() -> None:
    sample = f'key "transfer" {{ algorithm hmac-sha512; secret "{SECRET}"; }};'
    data: JsonValue = {"configuration": sample, "secret": SECRET}

    filtered = SecretFieldFilter().filter(data, Disclosure(include_authorization_code=True))

    assert isinstance(filtered, dict)
    assert filtered["configuration"] == (
        f'key "transfer" {{ algorithm hmac-sha512; secret "{HIDDEN_IN_TEXT}"; }};'
    )
    assert SECRET not in json.dumps(filtered)


def test_a_longer_secret_is_replaced_before_a_shorter_one_it_contains() -> None:
    data: JsonValue = {"a": {"secret": "abc"}, "b": {"secret": "abcdef"}, "text": "x abcdef y"}

    filtered = SecretFieldFilter().filter(data, Disclosure())

    assert isinstance(filtered, dict)
    assert filtered["text"] == f"x {HIDDEN_IN_TEXT} y"


def test_empty_secrets_and_other_data_are_kept() -> None:
    data: JsonValue = {"secret": "", "name": "zone", "count": 3, "none": None, "ok": True}

    assert SecretFieldFilter().filter(data, Disclosure()) == data
