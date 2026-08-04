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

