# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Exceptions of the domains notion."""


class DomainError(Exception):
    """Base class of the domain errors."""


class InvalidDomainNameError(DomainError):
    """A domain, host or TLD name is not a valid internationalized name."""


class InvalidDomainInputError(DomainError):
    """A value given for a domain operation is out of its bounds or format."""
