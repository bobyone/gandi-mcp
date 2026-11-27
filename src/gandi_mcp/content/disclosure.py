# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of what a caller explicitly asked to see in a Gandi result."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Disclosure:
    """Data hidden from the model by default, that the user asked to see.

    Attributes:
        include_contact_details: Full domain contacts instead of their summary.
        include_authorization_code: The authorization code of a domain.
    """

    include_contact_details: bool = False
    include_authorization_code: bool = False
