from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..api_client import ZoomClient


def register(mcp: FastMCP, client_factory: Callable[[], ZoomClient | None]) -> None:
    from . import contact_groups, divisions, groups, users

    contact_groups.register(mcp, client_factory)
    divisions.register(mcp, client_factory)
    groups.register(mcp, client_factory)
    users.register(mcp, client_factory)
