# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Exceptions of the accounts notion."""


class AccountError(Exception):
    """Base class of the account errors."""


class InvalidAccountNameError(AccountError):
    """Raised when an account name is empty, too long or has forbidden characters."""


class DuplicateAccountError(AccountError):
    """Raised when an account name is already used, ignoring case."""


class AccountNotFoundError(AccountError):
    """Raised when no account has the given name."""


class NoAccountError(AccountError):
    """Raised when an account is needed but none is configured."""


class ReadOnlyAccountError(AccountError):
    """Raised when a write operation targets a read-only account."""


class TokenRejectedError(AccountError):
    """Raised when Gandi refuses a Personal Access Token in the chosen environment."""
