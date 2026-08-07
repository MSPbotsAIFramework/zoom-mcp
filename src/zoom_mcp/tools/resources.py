from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..api_client import ZoomClient


def register(mcp: FastMCP, client_factory: Callable[[], ZoomClient | None]) -> None:
    from . import groups, users

    groups.register(mcp, client_factory)
    users.register(mcp, client_factory)
