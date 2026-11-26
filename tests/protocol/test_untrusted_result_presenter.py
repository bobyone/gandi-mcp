# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the framing of Gandi results."""

from gandi_mcp.domains.page_request import PageRequest
from gandi_mcp.operations.untrusted_result import UntrustedResult
from gandi_mcp.protocol.untrusted_result_presenter import UNTRUSTED_NOTICE, present


def test_frames_data_as_untrusted() -> None:
    assert present(UntrustedResult({"fqdn": "example.com"})) == {
        "notice": UNTRUSTED_NOTICE,
        "untrusted_data": {"fqdn": "example.com"},
    }


def test_lists_carry_their_page_and_total() -> None:
    framed = present(UntrustedResult([1, 2], 42), page=PageRequest(2, 2))

    assert framed["page"] == 2
    assert framed["per_page"] == 2
    assert framed["total_count"] == 42


def test_filtered_data_replaces_the_raw_data() -> None:
    framed = present(UntrustedResult({"a": 1}), data={"a": "hidden"}, page=PageRequest())

    assert framed["untrusted_data"] == {"a": "hidden"}
    assert "total_count" not in framed
