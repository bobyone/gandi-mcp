# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Exceptions of the secrets notion. Messages never contain a secret."""


class SecretStoreError(Exception):
    """Base class of the secret store errors."""


class SecretStoreUnavailableError(SecretStoreError):
    """Raised when the operating system keyring cannot be used."""


class SecretNotFoundError(SecretStoreError):
    """Raised when no secret is stored under a key."""


class InvalidTokenFormatError(SecretStoreError):
    """Raised when a Personal Access Token has an invalid format."""
