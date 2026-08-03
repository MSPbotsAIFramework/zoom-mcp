import contextvars
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from .api_client import ZoomClient
from .config import Settings

# Per-request credential isolation via contextvars.
# GatewayTokenMiddleware sets this before the MCP handler runs.
# Python asyncio copies context per task, so concurrent SSE connections are isolated.
_gateway_creds_var: contextvars.ContextVar[tuple[str, str, str] | None] = contextvars.ContextVar(
    "zoom_gateway_creds", default=None
)

REQUIRED_HEADERS = [
    "X-Zoom-Account-Id",
    "X-Zoom-Client-Id",
    "X-Zoom-Client-Secret",
]


def get_client_from_context(settings: Settings) -> ZoomClient | None:
    """Resolve the active ZoomClient for the current request context."""
    creds = _gateway_creds_var.get()
    if not creds:
        return None
    account_id, client_id, client_secret = creds
    return ZoomClient(
        account_id, client_id, client_secret, settings.zoom_oauth_url, settings.zoom_api_base_url
    )


class GatewayTokenMiddleware:
    """ASGI middleware.

    Reads X-Zoom-Account-Id, X-Zoom-Client-Id, and X-Zoom-Client-Secret
    (all required — Zoom's Server-to-Server OAuth "account_credentials"
    app credentials) from request headers and stores them in the
    contextvar. Returns 401 if any is missing on /mcp requests.
    """

    def __init__(self, app: ASGIApp, settings: Settings):
        self.app = app
        self.settings = settings

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if not path.startswith("/mcp"):
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        account_id = request.headers.get("x-zoom-account-id")
        client_id = request.headers.get("x-zoom-client-id")
        client_secret = request.headers.get("x-zoom-client-secret")
        if not all([account_id, client_id, client_secret]):
            response = JSONResponse(
                {
                    "error": "Missing credentials",
                    "message": f"This server requires the {', '.join(REQUIRED_HEADERS)} headers",
                    "required_headers": REQUIRED_HEADERS,
                    "optional_headers": [],
                },
                status_code=401,
            )
            await response(scope, receive, send)
            return

        ctx_token = _gateway_creds_var.set((account_id, client_id, client_secret))
        try:
            await self.app(scope, receive, send)
        finally:
            _gateway_creds_var.reset(ctx_token)


def create_mcp_server(settings: Settings) -> FastMCP:
    """Build the FastMCP server instance and register all Zoom tools."""
    # DNS-rebinding protection is a browser-oriented safeguard that rejects
    # non-localhost Host headers with 421. Disable it so the server works
    # correctly behind a reverse proxy or docker network.
    mcp = FastMCP(
        name="zoom-mcp",
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    )

    client_factory: Callable[[], ZoomClient | None] = lambda: get_client_from_context(settings)

    from .tools import resources

    resources.register(mcp, client_factory)

    return mcp
