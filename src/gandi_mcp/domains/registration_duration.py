# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of a registration or renewal duration."""

from dataclasses import dataclass

from gandi_mcp.domains.exceptions import InvalidDomainInputError

MIN_YEARS = 1
MAX_YEARS = 10


@dataclass(frozen=True)
class RegistrationDuration:
    """A number of years, from 1 to 10; each extension may allow fewer."""

    years: int

    def __post_init__(self) -> None:
        if isinstance(self.years, bool) or not MIN_YEARS <= self.years <= MAX_YEARS:
            raise InvalidDomainInputError(f"a duration is {MIN_YEARS} to {MAX_YEARS} years")
