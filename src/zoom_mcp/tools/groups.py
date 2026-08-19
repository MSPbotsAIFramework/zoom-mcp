from collections.abc import Callable
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .._json import dump_json_capped
from ..api_client import ZoomClient, ZoomError
from ._common import NO_TOKEN

# Zoom's own OpenAPI spec (developers.zoom.us/api-hub/users/methods/endpoints.json)
# documents these per-endpoint page_size ceilings; they differ per endpoint so each
# is clamped independently rather than sharing one constant.
_GROUPS_MAX_PAGE_SIZE = 300
_GROUP_MEMBERS_MAX_PAGE_SIZE = 2000


def register(mcp: FastMCP, client_factory: Callable[[], ZoomClient | None]) -> None:

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def zoom_list_groups(
        page_size: Annotated[
            int | None, Field(description="Records per page (max 300).")
        ] = None,
        next_page_token: Annotated[
            str | None,
            Field(description="Token from a previous response to fetch the next page."),
        ] = None,
    ) -> str:
        """List the account's user groups."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        if page_size is not None:
            page_size = min(page_size, _GROUPS_MAX_PAGE_SIZE)
        try:
            result = await client.list_groups(page_size=page_size, next_page_token=next_page_token)
            return dump_json_capped(result)
        except ZoomError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
    async def zoom_create_a_group(
        name: Annotated[str | None, Field(description="The new group's name.")] = None,
    ) -> str:
        """Create a new user group."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.create_a_group(name=name)
            return dump_json_capped(result)
        except ZoomError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def zoom_get_a_group(
        group_id: Annotated[str, Field(description="The group's ID, from zoom_list_groups.")],
    ) -> str:
        """Get a single group's details by ID."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get_a_group(group_id=group_id)
            return dump_json_capped(result)
        except ZoomError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=True))
    async def zoom_update_a_group(
        group_id: Annotated[str, Field(description="The group's ID, from zoom_list_groups.")],
        name: Annotated[
            str | None,
            Field(description="New group name. Must be unique on the account, under 128 chars."),
        ] = None,
    ) -> str:
        """Rename an existing group."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.update_a_group(group_id=group_id, name=name)
            return dump_json_capped(result)
        except ZoomError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def zoom_list_group_members(
        group_id: Annotated[str, Field(description="The group's ID, from zoom_list_groups.")],
        page_size: Annotated[
            int | None, Field(description="Records per page (max 2000, default 30).")
        ] = 30,
        page_number: Annotated[
            int | None,
            Field(description="Deprecated by Zoom; prefer next_page_token instead."),
        ] = None,
        next_page_token: Annotated[
            str | None,
            Field(description="Token from a previous response to fetch the next page."),
        ] = None,
    ) -> str:
        """List the members of a group."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        if page_size is not None:
            page_size = min(page_size, _GROUP_MEMBERS_MAX_PAGE_SIZE)
        try:
            result = await client.list_group_members(
                group_id=group_id,
                page_size=page_size,
                page_number=page_number,
                next_page_token=next_page_token,
            )
            return dump_json_capped(result)
        except ZoomError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
    async def zoom_add_group_members(
        group_id: Annotated[str, Field(description="The group's ID, from zoom_list_groups.")],
        members: Annotated[
            list[dict] | None,
            Field(
                description=(
                    "Members to add, each an object with an 'id' or 'email' field "
                    "identifying an existing user."
                )
            ),
        ] = None,
    ) -> str:
        """Add one or more existing users to a group."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.add_group_members(group_id=group_id, members=members)
            return dump_json_capped(result)
        except ZoomError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=True))
    async def zoom_delete_a_group_member(
        group_id: Annotated[str, Field(description="The group's ID, from zoom_list_groups.")],
        member_id: Annotated[str, Field(description="The member's user ID or email address.")],
    ) -> str:
        """Remove a member from a group. Irreversible; does not delete the user account."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.delete_a_group_member(group_id=group_id, member_id=member_id)
            return dump_json_capped(result)
        except ZoomError as e:
            return e.to_envelope()
