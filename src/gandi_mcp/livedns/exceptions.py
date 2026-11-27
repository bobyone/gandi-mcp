# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Exceptions of the LiveDNS notion."""


class LiveDnsError(Exception):
    """Base class of the LiveDNS errors."""


class InvalidRecordError(LiveDnsError):
    """A record name, type or value is not valid."""


class InvalidLiveDnsInputError(LiveDnsError):
    """A value given for a LiveDNS operation is out of its bounds or format."""
