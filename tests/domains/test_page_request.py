# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the page requests."""

import pytest

from gandi_mcp.domains.exceptions import InvalidDomainInputError
from gandi_mcp.domains.page_request import MAX_PAGE, MAX_PER_PAGE, PageRequest


def test_default_and_query() -> None:
    assert PageRequest().query() == {"page": 1, "per_page": 25}
    assert PageRequest(MAX_PAGE, MAX_PER_PAGE).query() == {"page": MAX_PAGE, "per_page": 100}


@pytest.mark.parametrize(("page", "per_page"), [(0, 10), (MAX_PAGE + 1, 10), (1, 0), (1, 101)])
def test_rejects_out_of_bounds(page: int, per_page: int) -> None:
    with pytest.raises(InvalidDomainInputError):
        PageRequest(page, per_page)
