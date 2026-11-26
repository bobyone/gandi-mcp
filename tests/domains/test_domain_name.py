# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the domain, host and TLD names."""

import pytest

from gandi_mcp.domains.domain_name import DomainName, HostLabel, TldName
from gandi_mcp.domains.exceptions import InvalidDomainNameError

BUCHER = "b\N{LATIN SMALL LETTER U WITH DIAERESIS}cher.de"


@pytest.mark.parametrize(
    ("raw", "ascii_form", "unicode_form"),
    [
        ("Example.COM", "example.com", "example.com"),
        ("example.com.", "example.com", "example.com"),
        (BUCHER, "xn--bcher-kva.de", BUCHER),
        ("xn--bcher-kva.de", "xn--bcher-kva.de", BUCHER),
        ("  www.example.org ", "www.example.org", "www.example.org"),
    ],
)
def test_normalizes_domain_names(raw: str, ascii_form: str, unicode_form: str) -> None:
    name = DomainName(raw)

    assert (name.value, name.unicode, str(name)) == (ascii_form, unicode_form, ascii_form)


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "localhost",
        "a..b",
        "-a.com",
        "exa mple.com",
        "ex_ample.com",
        "*.example.com",
        "../etc.com",
        "a/b.com",
        "a" * 64 + ".com",
        ("a" * 60 + ".") * 5 + "com",
    ],
)
def test_rejects_invalid_domain_names(raw: str) -> None:
    with pytest.raises(InvalidDomainNameError):
        DomainName(raw)


def test_domain_names_compare_by_ascii_form() -> None:
    assert DomainName(BUCHER) == DomainName("xn--bcher-kva.de")
    assert DomainName("a.com") != DomainName("b.com")


def test_tld_names() -> None:
    assert str(TldName(".FR")) == "fr"
    assert TldName("xn--p1ai").value == "xn--p1ai"
    for raw in ("", "co.uk", "a b"):
        with pytest.raises(InvalidDomainNameError):
            TldName(raw)


def test_host_labels() -> None:
    assert str(HostLabel("@")) == "@"
    assert str(HostLabel("NS1")) == "ns1"
    assert str(HostLabel("ns1.sub")) == "ns1.sub"
    for raw in ("", "a/b", "../x", "under_score"):
        with pytest.raises(InvalidDomainNameError):
            HostLabel(raw)
