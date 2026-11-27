# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Media types of the Gandi API answers."""

from enum import StrEnum


class MediaType(StrEnum):
    """What a request asks Gandi to answer with (``Accept`` header).

    ``JSON`` answers are decoded; ``TEXT`` answers (zone files) are kept as a string.
    """

    JSON = "application/json"
    TEXT = "text/plain"
