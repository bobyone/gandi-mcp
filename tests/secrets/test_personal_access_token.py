# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the Personal Access Token value object."""

import pickle

import pytest

from gandi_mcp.secrets.exceptions import InvalidTokenFormatError
from gandi_mcp.secrets.personal_access_token import MAX_LENGTH, MIN_LENGTH, PersonalAccessToken

VALUE = "pat_0123456789abcdef-XYZ"


def test_reveals_the_value() -> None:
    assert PersonalAccessToken(VALUE).reveal() == VALUE


def test_is_masked_in_repr_str_and_formatting() -> None:
    token = PersonalAccessToken(VALUE)

    for text in (repr(token), str(token), f"{token}", f"{token!r}", repr([token])):
        assert VALUE not in text
        assert "****" in text


def test_compares_by_value() -> None:
    assert PersonalAccessToken(VALUE) == PersonalAccessToken(VALUE)
    assert PersonalAccessToken(VALUE) != PersonalAccessToken(VALUE + "x")
    assert PersonalAccessToken(VALUE) != VALUE
    assert hash(PersonalAccessToken(VALUE)) == hash(PersonalAccessToken(VALUE))


def test_cannot_be_serialized() -> None:
    with pytest.raises(TypeError):
        pickle.dumps(PersonalAccessToken(VALUE))


@pytest.mark.parametrize(
    "value",
    [
        "",
        "a" * (MIN_LENGTH - 1),
        "a" * (MAX_LENGTH + 1),
        "pat_0123456789 abcdef",
        "pat_0123456789abcdef\n",
        "pat_0123456789abcd\N{LATIN SMALL LETTER E WITH ACUTE}",
        "pat_0123456789abcdef\x00",
    ],
)
def test_rejects_invalid_formats(value: str) -> None:
    with pytest.raises(InvalidTokenFormatError) as raised:
        PersonalAccessToken(value)

    assert not value or value not in str(raised.value)


def test_accepts_the_bounds() -> None:
    PersonalAccessToken("a" * MIN_LENGTH)
    PersonalAccessToken("a" * MAX_LENGTH)
