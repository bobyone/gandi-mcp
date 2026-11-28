# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tool parameters and results shared by the LiveDNS tools."""

from typing import Annotated, Any

from pydantic import BaseModel, Field

from gandi_mcp.accounts.organization_id import OrganizationId
from gandi_mcp.files.written_file import WrittenFile
from gandi_mcp.livedns.record import Record

LiveDnsDomainParameter = Annotated[
    str,
    Field(
        description="Domain whose zone is served by LiveDNS, e.g. example.com (Unicode accepted).",
        max_length=253,
    ),
]
RecordNameParameter = Annotated[
    str,
    Field(
        description="Record name relative to the zone: @ for the domain itself, www, "
        "*.dev, _dmarc.",
        max_length=253,
    ),
]
RecordTypeParameter = Annotated[
    str, Field(description="Record type, e.g. A, AAAA, MX, TXT, CNAME.", max_length=10)
]
SharingIdParameter = Annotated[
    str | None,
    Field(
        default=None,
        description="Organization to act for, if not the user's own (from list_organizations).",
        max_length=36,
    ),
]
FileParameter = Annotated[
    str,
    Field(
        description="File to write, relative to the gandi-mcp work directory (subdirectories "
        "allowed, e.g. zones/example.com.zone).",
        min_length=1,
        max_length=255,
    ),
]
OverwriteParameter = Annotated[
    bool, Field(description="Replace the file if it exists. Only when the user asks for it.")
]

EXPORT_NOTICE = (
    "The content was written to the file and not shown here: it is data from Gandi, "
    "untrusted. The file is in the gandi-mcp work directory."
)


def sharing_id(value: str | None) -> str | None:
    """Validate an organization identifier given as ``sharing_id``."""
    return str(OrganizationId(value)) if value else None


def exported(written: WrittenFile, **details: int) -> dict[str, Any]:
    """Describe a written file for the model, without its content nor its full path."""
    return {
        "status": "done",
        "notice": EXPORT_NOTICE,
        "file": written.relative_path,
        "size_bytes": written.size,
        **details,
    }


class RecordParameter(BaseModel):
    """A record given by the model: name, type, values and optional TTL."""

    name: str = Field(
        description="Name relative to the zone: @, www, *.dev, _dmarc.", max_length=253
    )
    type: str = Field(description="Record type, e.g. A, MX, TXT.", max_length=10)
    values: list[str] = Field(
        description="Values as LiveDNS writes them, e.g. 192.0.2.1 or 10 mail.example.com.; "
        "TXT values in double quotes.",
        min_length=1,
        max_length=100,
    )
    ttl: int | None = Field(default=None, description="TTL in seconds, 300 to 2592000.")

    def record(self) -> Record:
        """The validated record."""
        return Record.of(self.name, self.type, self.values, self.ttl)


RecordValuesParameter = Annotated[
    list[str],
    Field(
        description="Values as LiveDNS writes them, e.g. 192.0.2.1 or 10 mail.example.com.; "
        "TXT values in double quotes.",
        min_length=1,
        max_length=100,
    ),
]
TtlParameter = Annotated[
    int | None, Field(default=None, description="TTL in seconds, 300 to 2592000.")
]


class TypedRecordParameter(BaseModel):
    """A record of a given name: its type, values and optional TTL."""

    type: str = Field(description="Record type, e.g. A, MX, TXT.", max_length=10)
    values: list[str] = Field(
        description="Values as LiveDNS writes them; TXT values in double quotes.",
        min_length=1,
        max_length=100,
    )
    ttl: int | None = Field(default=None, description="TTL in seconds, 300 to 2592000.")

    def record(self, name: str) -> Record:
        """The validated record of ``name``."""
        return Record.of(name, self.type, self.values, self.ttl)
