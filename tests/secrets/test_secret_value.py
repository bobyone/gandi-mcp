# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the secrets typed by the user."""

import pickle

import pytest

from gandi_mcp.secrets.exceptions import InvalidSecretValueError
from gandi_mcp.secrets.secret_value import SecretValue


def test_the_value_is_never_shown() -> None:
    secret = SecretValue("Auth-Code_123!")

    assert secret.reveal() == "Auth-Code_123!"
    assert "Auth" not in repr(secret)
    assert "Auth" not in str(secret)
    assert "Auth" not in f"{[secret]}"
    with pytest.raises(TypeError):
        pickle.dumps(secret)


def test_equality_and_hash() -> None:
    assert SecretValue("été") == SecretValue("été")
    assert SecretValue("a") != SecretValue("b")
    assert SecretValue("a") != "a"
    assert len({SecretValue("a"), SecretValue("a")}) == 1


@pytest.mark.parametrize("value", ["", "x" * 11, "line\nbreak", "tab\t", "nul\x00"])
def test_invalid_values_are_refused(value: str) -> None:
    with pytest.raises(InvalidSecretValueError):
        SecretValue(value, max_length=10)
