# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the record name value object."""

import pytest

from gandi_mcp.livedns.exceptions import InvalidRecordError
from gandi_mcp.livedns.record_name import RecordName


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        ("@", "@"),
        (" @ ", "@"),
        ("www", "www"),
        ("WWW", "www"),
        ("*.dev", "*.dev"),
        ("*", "*"),
        ("_dmarc", "_dmarc"),
        ("_acme-challenge.www", "_acme-challenge.www"),
        ("selector1._domainkey", "selector1._domainkey"),
        ("bücher", "xn--bcher-kva"),
    ],
)
def test_valid_names_are_kept_in_ascii_form(given: str, expected: str) -> None:
    assert RecordName(given).value == expected


@pytest.mark.parametrize(
    "given",
    [
        "",
        "   ",
        "www.",
        "a..b",
        "www/../admin",
        "a/b",
        "dev.*",
        "-www",
        "www-",
        "a b",
        "x" * 64,
        ".".join(["a" * 63] * 4) + "a",
        "%2e%2e",
        "\n",
        "a\uff0eb",
        "\ufffd",
        ".".join(["ü"] * 60),
    ],
)
def test_invalid_names_are_refused(given: str) -> None:
    with pytest.raises(InvalidRecordError):
        RecordName(given)


def test_a_name_reads_as_its_ascii_form() -> None:
    assert str(RecordName("Bücher")) == "xn--bcher-kva"
