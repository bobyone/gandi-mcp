# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tool parameters specific to the Domain API tools."""

from typing import Annotated

from pydantic import Field

DomainParameter = Annotated[
    str, Field(description="Domain name, e.g. example.com (Unicode accepted).", max_length=253)
]

ContactDetailsParameter = Annotated[
    bool,
    Field(
        description="Return the full contact details (names, addresses, emails). Only when "
        "the user asks for them: by default only the type and country of each contact."
    ),
]

AuthorizationCodeParameter = Annotated[
    bool,
    Field(
        description="Return the authorization code needed to transfer the domain to "
        "another registrar. Only when the user asks for it."
    ),
]
