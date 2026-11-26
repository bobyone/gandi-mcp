# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the values of the domain settings."""

import pytest

from gandi_mcp.domains.exceptions import InvalidDomainInputError
from gandi_mcp.domains.write_values import (
    DnssecKeyId,
    DnssecKeySpec,
    DnssecKeyType,
    EmailAddress,
    IpAddress,
    RedirectionUrl,
    TagName,
)


def test_valid_values() -> None:
    assert IpAddress(" 2001:DB8:0:0:0:0:0:FF ").value == "2001:db8::ff"
    assert IpAddress("203.0.113.2").value == "203.0.113.2"
    key = DnssecKeySpec(13, DnssecKeyType.ZSK, "AAECAwQFBgcICQoLDA0O DxAREhMUFRYXGBkaGxwdHh8=")
    assert key.to_json() == {
        "algorithm": 13,
        "type": "zsk",
        "public_key": "AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8=",
    }
    assert DnssecKeyId(" 12-ab_C ").value == "12-ab_C"
    assert TagName("  to   renew ").value == "to renew"
    assert RedirectionUrl(" https://www.example.org/path?q=1 ").value == (
        "https://www.example.org/path?q=1"
    )
    assert EmailAddress(" alice@example.org ").value == "alice@example.org"


@pytest.mark.parametrize(
    "build",
    [
        lambda: IpAddress("300.1.1.1"),
        lambda: DnssecKeySpec(256, DnssecKeyType.KSK, "AAAA"),
        lambda: DnssecKeySpec(True, DnssecKeyType.KSK, "AAAA"),
        lambda: DnssecKeySpec(13, DnssecKeyType.KSK, ""),
        lambda: DnssecKeySpec(13, DnssecKeyType.KSK, "not base64!"),
        lambda: DnssecKeyId("../x"),
        lambda: TagName(""),
        lambda: TagName("x" * 101),
        lambda: TagName("bell\x07"),
        lambda: RedirectionUrl("ftp://example.org/"),
        lambda: RedirectionUrl("javascript:alert(1)"),
        lambda: RedirectionUrl("https://exa mple.org/"),
        lambda: RedirectionUrl("https://localhost/"),
        lambda: RedirectionUrl("https://example.org/" + "x" * 2048),
        lambda: EmailAddress("alice"),
    ],
)
def test_invalid_values(build: object) -> None:
    with pytest.raises(InvalidDomainInputError):
        build()  # type: ignore[operator]
