# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the account name value object."""

import pytest

from gandi_mcp.accounts.account_name import MAX_LENGTH, AccountName
from gandi_mcp.accounts.exceptions import InvalidAccountNameError


@pytest.mark.parametrize(
    ("raw", "normalized"),
    [
        ("Perso", "Perso"),
        ("  Société 2  ", "Société 2"),
        ("e\N{COMBINING ACUTE ACCENT}t\N{LATIN SMALL LETTER E WITH ACUTE}", "été"),
        ("Работа", "Работа"),
        ("my-shop", "my-shop"),
        ("a" * MAX_LENGTH, "a" * MAX_LENGTH),
    ],
)
def test_normalizes_valid_names(raw: str, normalized: str) -> None:
    assert AccountName(raw).value == normalized
    assert str(AccountName(raw)) == normalized


@pytest.mark.parametrize(
    "raw",
    ["", "   ", "a" * (MAX_LENGTH + 1), "two  spaces", "under_score", "dot.", "tab\tname", "<b>"],
)
def test_rejects_invalid_names(raw: str) -> None:
    with pytest.raises(InvalidAccountNameError):
        AccountName(raw)


def test_names_differing_by_case_are_equal() -> None:
    assert AccountName("Perso") == AccountName("PERSO")
    assert hash(AccountName("Perso")) == hash(AccountName("perso"))
    assert AccountName("Perso") != AccountName("Pro")
    assert AccountName("Perso") != "Perso"
