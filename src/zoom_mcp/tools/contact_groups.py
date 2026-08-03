import json
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..api_client import ZoomClient, ZoomError
from ._common import NO_TOKEN


def register(mcp: FastMCP, client_factory: Callable[[], ZoomClient | None]) -> None:

    @mcp.tool()
    async def zoom_list_contact_groups(page_size: int = 10, next_page_token: str | None = None) -> str:
        """List contact groups

API: GET /contacts/groups

Args:
    page_size: Optional. The number of records returned with a single API call.
    next_page_token: Optional. The next page token is used to paginate through large
        result sets. A next page token will be returned whenever the set of available
        results exceeds the current page size. The expiration period for this token is
        15 minutes.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.list_contact_groups(page_size=page_size, next_page_token=next_page_token)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_create_a_contact_group(group_name: str | None = None, group_privacy: int | None = None, description: str | None = None, group_members: list[dict] | None = None) -> str:
        """Create a contact group

API: POST /contacts/groups

Args:
    group_name: Optional. The contact group's name.
    group_privacy: Optional. Contact group privacy configuration: `1` - Visible to
        anyone, searchable by anyone. `2` - Visible to members only, searchable by
        anyone. `3` - Visible to members only, searchable by members only. One of: [1,
        2, 3].
    description: Optional. The group description.
    group_members: Optional.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.create_a_contact_group(group_name=group_name, group_privacy=group_privacy, description=description, group_members=group_members)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_get_a_contact_group(group_id: str) -> str:
        """Get a contact group

API: GET /contacts/groups/{groupId}

Args:
    group_id: Required. The contact group ID. Retrieve by calling the [**List contact
        groups**](/docs/api-reference/zoom-api/methods#operation/contactGroups) API.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get_a_contact_group(group_id=group_id)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_delete_a_contact_group(group_id: str) -> str:
        """Delete a contact group

API: DELETE /contacts/groups/{groupId}

Args:
    group_id: Required. The contact group ID. Retrieve by calling the [**List contact
        groups**](/docs/api-reference/zoom-api/methods#operation/contactGroups) API.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.delete_a_contact_group(group_id=group_id)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_update_a_contact_group(group_id: str, name: str | None = None, privacy: int | None = None, description: str | None = None) -> str:
        """Update a contact group

API: PATCH /contacts/groups/{groupId}

Args:
    group_id: Required. The contact group ID. Retrieve by calling the [**List contact
        groups**](/docs/api-reference/zoom-api/methods#operation/contactGroups) API.
    name: Optional. The contact group's name.
    privacy: Optional. Contact group privacy configuration: `1` - Visible to anyone,
        searchable by anyone. `2` - Visible to members only, searchable by anyone. `3` -
        Visible to members only, searchable by members only. One of: [1, 2, 3].
    description: Optional. The group description.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.update_a_contact_group(group_id=group_id, name=name, privacy=privacy, description=description)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_list_contact_group_members(group_id: str, page_size: int = 10, next_page_token: str | None = None) -> str:
        """List contact group members

API: GET /contacts/groups/{groupId}/members

Args:
    group_id: Required. The group ID.
    page_size: Optional. The number of records returned with a single API call.
    next_page_token: Optional. The next page token is used to paginate through large
        result sets. A next page token will be returned whenever the set of available
        results exceeds the current page size. The expiration period for this token is
        15 minutes.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.list_contact_group_members(group_id=group_id, page_size=page_size, next_page_token=next_page_token)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_add_contact_group_members(group_id: str, group_members: list[dict] | None = None) -> str:
        """Add contact group members

API: POST /contacts/groups/{groupId}/members

Args:
    group_id: Required. The contact group ID. Retrieve by calling the List contact
        groups API.
    group_members: Optional. Group members array
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.add_contact_group_members(group_id=group_id, group_members=group_members)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_remove_members_in_a_contact_group(group_id: str, member_ids: str) -> str:
        """Remove members in a contact group

API: DELETE /contacts/groups/{groupId}/members

Args:
    group_id: Required. The contact group ID. Retrieve by calling the List contact
        groups API.
    member_ids: Required. The member's ID in a contact group. Use commas (,) to separate
        a maximum of 20 ids. Can be retrieved by calling the [**List contact
        groups**](/docs/api-reference/zoom-api/methods#operation/contactGroupMembers)
        API.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.remove_members_in_a_contact_group(group_id=group_id, member_ids=member_ids)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"
