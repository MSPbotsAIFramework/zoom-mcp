import json
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..api_client import ZoomClient, ZoomError
from ._common import NO_TOKEN


def register(mcp: FastMCP, client_factory: Callable[[], ZoomClient | None]) -> None:
    @mcp.tool()
    async def zoom_list_groups(page_size: int | None = None, next_page_token: str | None = None) -> str:
        """List groups

API: GET /groups

Args:
    page_size: Optional. The number of records returned in a single API call. The
        maximum is 300.
    next_page_token: Optional. The next page token paginates through a set of large
        results. A next page token is returned whenever the set of available results
        exceeds the current page size. The expiration period for this token is 15
        minutes.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.list_groups(page_size=page_size, next_page_token=next_page_token)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_create_a_group(name: str | None = None) -> str:
        """Create a group

API: POST /groups

Args:
    name: Optional. The group's name.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.create_a_group(name=name)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_get_a_group(group_id: str) -> str:
        """Get a group

API: GET /groups/{groupId}

Args:
    group_id: Required. The group ID. Retrieve by calling the [**List
        groups**](/docs/api-reference/zoom-api/methods#operation/groups) API.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get_a_group(group_id=group_id)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_update_a_group(group_id: str, name: str | None = None) -> str:
        """Update a group

API: PATCH /groups/{groupId}

Args:
    group_id: Required. The group ID. Retrieve by calling the [**List
        groups**](/docs/api-reference/zoom-api/methods#operation/groups) API.
    name: Optional. Group name. It must be unique to one account and less than 128
        characters.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.update_a_group(group_id=group_id, name=name)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_list_group_members(group_id: str, page_size: int = 30, page_number: int = 1, next_page_token: str | None = None) -> str:
        """List group members

API: GET /groups/{groupId}/members

Args:
    group_id: Required. The group ID. Retrieve by calling the [**List
        groups**](/docs/api-reference/zoom-api/methods#operation/groups) API.
    page_size: Optional. The number of records returned within a single API call.
    page_number: Optional. **Deprecated.** We will no longer support this field in a
        future release. Instead, use the `next_page_token` for pagination.
    next_page_token: Optional. Use the next page token to paginate through large result
        sets. A next page token is returned whenever the set of available results
        exceeds the current page size. This token's expiration period is 15 minutes.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.list_group_members(group_id=group_id, page_size=page_size, page_number=page_number, next_page_token=next_page_token)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_add_group_members(group_id: str, members: list[dict] | None = None) -> str:
        """Add group members

API: POST /groups/{groupId}/members

Args:
    group_id: Required. The group ID. Retrieve by calling the [**List
        groups**](/docs/api-reference/zoom-api/methods#operation/groups) API.
    members: Optional. List of Group members
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.add_group_members(group_id=group_id, members=members)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_delete_a_group_member(group_id: str, member_id: str) -> str:
        """Delete a group member

API: DELETE /groups/{groupId}/members/{memberId}

Args:
    group_id: Required. The group ID. Retrieve by calling the [**List
        groups**](/docs/api-reference/zoom-api/methods#operation/groups) API.
    member_id: Required. The member ID or email address.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.delete_a_group_member(group_id=group_id, member_id=member_id)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

