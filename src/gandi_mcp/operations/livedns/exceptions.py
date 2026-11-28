# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Exceptions of the LiveDNS operations."""


class ZoneChangeError(Exception):
    """Base class of the errors of a zone change."""


class SnapshotFailedError(ZoneChangeError):
    """The snapshot asked before a zone change could not be taken: nothing was changed."""


class TooManyRecordsError(ZoneChangeError):
    """A zone replacement gives more records than one call accepts."""
