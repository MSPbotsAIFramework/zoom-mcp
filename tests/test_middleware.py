"""Gateway credential middleware tests: missing-header 401, and header
values correctly reaching the per-request contextvar (no global-state
leakage across requests).
"""

from starlette.testclient import TestClient

from zoom_mcp.__main__ import _build_http_app
from zoom_mcp.config import Settings
from zoom_mcp.server import create_mcp_server, get_client_from_context


def _make_app():
    settings = Settings()
    mcp = create_mcp_server(settings)
    return _build_http_app(mcp, settings), settings


def test_health_is_local_and_does_not_require_credentials():
    app, _ = _make_app()
    with TestClient(app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


def test_missing_header_returns_401_with_required_headers_listed():
    app, _ = _make_app()
    with TestClient(app) as client:
        resp = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
            headers={"Accept": "application/json, text/event-stream"},
        )
        assert resp.status_code == 401
        body = resp.json()
        for header in ("X-Zoom-Account-Id", "X-Zoom-Client-Id", "X-Zoom-Client-Secret"):
            assert header in body["required_headers"]


def test_partial_headers_still_returns_401():
    # Only one of the three required headers present — must still be rejected,
    # not silently proceed with an incomplete credential set.
    app, _ = _make_app()
    with TestClient(app) as client:
        resp = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
            headers={
                "Accept": "application/json, text/event-stream",
                "X-Zoom-Account-Id": "acct-123",
            },
        )
        assert resp.status_code == 401


def test_header_present_reaches_request_context():
    # Directly exercises the middleware's contextvar plumbing without a full
    # MCP protocol round-trip: confirms the header values that arrive on the
    # request are exactly what get_client_from_context sees, and that they're
    # reset afterward (no leakage to the next request).
    import asyncio

    from zoom_mcp.server import GatewayTokenMiddleware, _gateway_creds_var

    settings = Settings()
    seen = {}

    async def fake_app(scope, receive, send):
        seen["creds"] = _gateway_creds_var.get()
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    middleware = GatewayTokenMiddleware(fake_app, settings)

    async def run():
        scope = {
            "type": "http",
            "path": "/mcp",
            "headers": [
                (b"x-zoom-account-id", b"acct-123"),
                (b"x-zoom-client-id", b"client-abc"),
                (b"x-zoom-client-secret", b"secret-xyz"),
            ],
        }

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        sent = []

        async def send(message):
            sent.append(message)

        await middleware(scope, receive, send)

    asyncio.run(run())
    assert seen["creds"] == ("acct-123", "client-abc", "secret-xyz")
    # After the request completes, the contextvar must be reset — a fresh
    # get() outside any request context sees no leftover credential.
    assert _gateway_creds_var.get() is None


def test_client_factory_returns_none_without_context():
    settings = Settings()
    assert get_client_from_context(settings) is None
