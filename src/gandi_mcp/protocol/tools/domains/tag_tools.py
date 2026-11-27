# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Model tools changing the tags of a domain."""

from collections.abc import Callable
from typing import Annotated, Any

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from pydantic import Field

from gandi_mcp.domains.domain_name import DomainName
from gandi_mcp.domains.write_values import MAX_TAG_LENGTH, TagName
from gandi_mcp.gandi.gandi_response import JsonValue
from gandi_mcp.operations.domain import domain_endpoints
from gandi_mcp.operations.domain.domain_endpoint import DomainEndpoint
from gandi_mcp.protocol.tool_module import ToolModule
from gandi_mcp.protocol.tools.domains.domain_tool_runner import (
    AccountParameter,
    ConfirmationIdParameter,
    DomainParameter,
    DomainToolRunner,
    add_write_tool,
)

MAX_TAGS = 50
TagParameter = Annotated[str, Field(description="Tag text.", max_length=MAX_TAG_LENGTH)]
TagsParameter = Annotated[list[TagParameter], Field(description="Tags.", max_length=MAX_TAGS)]


def _tags(values: list[str]) -> list[JsonValue]:
    return [TagName(value).value for value in values]


class TagTools(ToolModule):
    """Add, replace, update and remove the tags of a domain."""

    def __init__(self, runner: DomainToolRunner) -> None:
        self._runner = runner

    def register(self, server: MCPServer) -> None:
        tools = (
            (self.domain_tag_add, domain_endpoints.TAG_ADD, "Tag a domain", "Add a tag."),
            (
                self.domain_tags_replace,
                domain_endpoints.TAGS_REPLACE,
                "Replace the tags of a domain",
                "Replace all the tags of a domain with the given list.",
            ),
            (
                self.domain_tags_update,
                domain_endpoints.TAGS_UPDATE,
                "Add and remove tags of a domain",
                "Add some tags to a domain and remove others.",
            ),
            (
                self.domain_tags_delete,
                domain_endpoints.TAGS_DELETE,
                "Remove all the tags of a domain",
                "Remove every tag of a domain.",
            ),
        )
        for function, endpoint, title, description in tools:
            add_write_tool(server, function, endpoint, title, description)

    async def domain_tag_add(
        self,
        domain: DomainParameter,
        tag: TagParameter,
        ctx: Context[Any, Any],
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Add a tag."""
        return await self._write(
            ctx, domain_endpoints.TAG_ADD, domain, account, lambda: {"tag": TagName(tag).value}
        )

    async def domain_tags_replace(
        self,
        domain: DomainParameter,
        tags: TagsParameter,
        ctx: Context[Any, Any],
        confirmation_id: ConfirmationIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Replace the tags, after confirmation (it can remove every tag)."""
        return await self._write(
            ctx,
            domain_endpoints.TAGS_REPLACE,
            domain,
            account,
            lambda: {"tags": _tags(tags)},
            confirmation_id=confirmation_id,
        )

    async def domain_tags_update(
        self,
        domain: DomainParameter,
        ctx: Context[Any, Any],
        *,
        add: TagsParameter = [],  # noqa: B006 - pydantic copies the default
        remove: TagsParameter = [],  # noqa: B006 - pydantic copies the default
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Add and remove tags."""
        return await self._write(
            ctx,
            domain_endpoints.TAGS_UPDATE,
            domain,
            account,
            lambda: {"add": _tags(add), "remove": _tags(remove)},
        )

    async def domain_tags_delete(
        self,
        domain: DomainParameter,
        ctx: Context[Any, Any],
        confirmation_id: ConfirmationIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Remove every tag."""
        return await self._write(
            ctx, domain_endpoints.TAGS_DELETE, domain, account, confirmation_id=confirmation_id
        )

    async def _write(
        self,
        ctx: Context[Any, Any],
        endpoint: DomainEndpoint,
        domain: str,
        account: str | None,
        body: Callable[[], JsonValue] | None = None,
        *,
        confirmation_id: str | None = None,
    ) -> dict[str, Any]:
        return await self._runner.write(
            ctx,
            endpoint,
            account,
            lambda: {"domain": DomainName(domain).value},
            body=body,
            confirmation_id=confirmation_id,
        )
