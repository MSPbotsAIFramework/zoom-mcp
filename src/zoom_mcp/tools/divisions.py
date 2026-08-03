import json
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..api_client import ZoomClient, ZoomError
from ._common import NO_TOKEN


def register(mcp: FastMCP, client_factory: Callable[[], ZoomClient | None]) -> None:

    @mcp.tool()
    async def zoom_list_divisions(next_page_token: str | None = None, page_size: int = 30) -> str:
        """List divisions

API: GET /divisions

Args:
    next_page_token: Optional. Use the next page token to paginate through a large set
        of results. It returns whenever the set of available results exceeds the current
        page size. This token's expiration period is 15 minutes.
    page_size: Optional. The number of records returned within a single API call.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.list_divisions(next_page_token=next_page_token, page_size=page_size)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_create_a_division(division_name: str, division_description: str | None = None) -> str:
        """Create a division

API: POST /divisions

Args:
    division_name: Required. The division's name.
    division_description: Optional. The division's description.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.create_a_division(division_name=division_name, division_description=division_description)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_get_a_division(division_id: str) -> str:
        """Get a division

API: GET /divisions/{divisionId}

Args:
    division_id: Required. The division's id
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get_a_division(division_id=division_id)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_delete_a_division(division_id: str) -> str:
        """Delete a division

API: DELETE /divisions/{divisionId}

Args:
    division_id: Required. The division's ID.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.delete_a_division(division_id=division_id)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_update_a_division(division_id: str, division_name: str | None = None, division_description: str | None = None) -> str:
        """Update a division

API: PATCH /divisions/{divisionId}

Args:
    division_id: Required. The division's ID.
    division_name: Optional. The division's name.
    division_description: Optional. The division's description.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.update_a_division(division_id=division_id, division_name=division_name, division_description=division_description)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_list_division_members(division_id: str, next_page_token: str | None = None, page_size: int = 30) -> str:
        """List division members

API: GET /divisions/{divisionId}/users

Args:
    division_id: Required. The division's ID.
    next_page_token: Optional. Use the next page token to paginate through a large set
        of results. It returns whenever the set of available results exceeds the current
        page size. This token's expiration period is 15 minutes.
    page_size: Optional. The number of records returned within a single API call.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.list_division_members(division_id=division_id, next_page_token=next_page_token, page_size=page_size)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_assign_a_division(division_id: str, users: list[dict] | None = None) -> str:
        """Assign a division

API: POST /divisions/{divisionId}/users

Args:
    division_id: Required. The division's ID.
    users: Optional. Array of userId/user email of users to whom you would like to
        assign this division. Up to 30 users can be assigned a division at once.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.assign_a_division(division_id=division_id, users=users)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"
