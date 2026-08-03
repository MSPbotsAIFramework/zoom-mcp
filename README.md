# zoom-mcp

MCP server for **Zoom**'s Users Admin REST API. Covers **account
creation and validation** (PRD-15547: "Onboarding step 20 — Account
creation / validation"), including group-driven provisioning.

> Naming note: Zoom also publishes its own first-party MCP servers
> (`developers.zoom.us/docs/mcp`) — Zoom, Whiteboard, Chat, Docs, Tasks,
> Canvas, Revenue Accelerator, Meetings. Investigated and confirmed those
> are scoped entirely to meeting/chat/document/whiteboard *content*
> access via per-user OAuth 2.1 (Claude/ChatGPT connector style) — none
> of them expose user/account administration. This server instead wraps
> Zoom's standard Admin REST API (`https://api.zoom.us/v2`) directly,
> which is the only place account creation/validation actually lives.

## Overview

- Stateless HTTP service. No credentials are ever persisted — each
  request supplies its own Server-to-Server OAuth app credentials via
  headers, used only for the lifetime of that single request.
- Supports concurrent requests; per-request credential isolation is done
  via Python `contextvars`, not a global/shared client instance.
- Entry points: `POST /mcp` (MCP protocol) and `GET /health` (health
  check).
- Default port: `8080` (configurable via `MCP_HTTP_PORT`).

## Authentication

Zoom's Users Admin API uses **Server-to-Server OAuth** (the
`account_credentials` grant — a fully backend two-legged OAuth flow,
no user redirect):

```
POST https://zoom.us/oauth/token?grant_type=account_credentials&account_id=<accountId>
Authorization: Basic base64(clientId:clientSecret)
-> {"access_token": "...", "expires_in": 3599, "token_type": "bearer"}
```

The access token is valid for only 1 hour and Zoom issues no refresh
token, so this server performs a **fresh token exchange on every single
tool call** rather than caching anything across MCP requests — the same
"re-authenticate every call" approach used by several other vendor-mcp
services in this fleet (webroot-mcp, tsheets-mcp, oitvoip-mcp,
covedataprotection-mcp) whose upstream tokens are similarly short-lived
or non-refreshable.

### HEADER 授权参数说明

| Header | 类型 | 是否必填 | 默认值 | 枚举值 | 字段描述 | Example |
|---|---|---|---|---|---|---|
| `X-Zoom-Account-Id` | string | 是 | 无 | 无 | Zoom Server-to-Server OAuth app 的 Account ID（Zoom App Marketplace -> Manage -> 该 app -> Basic Information -> App Credentials） | `Ab1CdEfGhIJkLmNoPq2rS` |
| `X-Zoom-Client-Id` | string | 是 | 无 | 无 | 同一个 S2S OAuth app 的 Client ID | `a1B2c3D4e5F6g7H8i9J0` |
| `X-Zoom-Client-Secret` | string | 是 | 无 | 无 | 同一个 S2S OAuth app 的 Client Secret | `k1L2m3N4o5P6q7R8s9T0u1V2` |

Missing any header returns `401`:
```json
{
  "error": "Missing credentials",
  "message": "This server requires the X-Zoom-Account-Id, X-Zoom-Client-Id, X-Zoom-Client-Secret headers",
  "required_headers": ["X-Zoom-Account-Id", "X-Zoom-Client-Id", "X-Zoom-Client-Secret"],
  "optional_headers": []
}
```

Invalid app credentials surface as a tool-level error from the token
exchange itself, e.g.:
```
Error: Zoom API error: HTTP 400 during login: {"reason":"Invalid client_id or client_secret","error":"invalid_client"}
```

Required scopes on the S2S OAuth app (set on the app's **Scopes** page
in the Zoom App Marketplace): `user:write:admin`, `user:read:admin`,
`group:read:admin`, `group:write:admin`.

## Environment Variables

| Variable | 类型 | 是否必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `MCP_HTTP_PORT` | int | 否 | `8080` | HTTP 监听端口 |
| `MCP_HTTP_HOST` | string | 否 | `0.0.0.0` | HTTP 监听地址 |
| `ZOOM_OAUTH_URL` | string | 否 | `https://zoom.us/oauth/token` | Zoom OAuth token 端点 |
| `ZOOM_API_BASE_URL` | string | 否 | `https://api.zoom.us/v2` | Zoom REST API 基础 URL |

## MCP Endpoint

- `POST /mcp` — MCP protocol (streamable HTTP transport)
- `GET /health` — health check, returns `{"status": "ok", "service": "zoom-mcp", "transport": "http"}`

## Tool List

| Tool | 功能 | 参数 |
|---|---|---|
| `zoom_create_user` | 创建新 Zoom 用户账号 | `email`（必填）、`user_type`（可选，默认 1=Basic，2=Licensed，4=Unassigned）、`action`（可选，默认 `create`，还可选 `autoCreate`/`custCreate`/`ssoCreate`）、`display_name`（可选）、`division_ids`（可选） |
| `zoom_check_user_email` | 校验某邮箱是否已在本账号下注册为 Zoom 用户（账号校验） | `email`（必填） |
| `zoom_get_user` | 按 userId/邮箱获取完整账号详情（账号校验） | `user_id`（必填）、`login_type`（可选） |
| `zoom_add_group_member` | 把已存在的用户加入某个 group，实现 group-driven 的账号 provisioning | `group_id`（必填）、`email` 或 `user_id`（二选一） |
| `zoom_list_groups` | 列出账号下所有 group，便于查找 `group_id` | 无 |

Responses are the vendor's raw JSON, pretty-printed, returned as-is.

## 测试示例

```bash
# Health check
curl -s http://localhost:8080/health

# Call a tool via the MCP protocol (streamable HTTP) — requires an
# initialize handshake first per the MCP spec; abbreviated example below
# shows the tool-call request body only:
curl -s -X POST http://localhost:8080/mcp \
  -H "X-Zoom-Account-Id: <your-account-id>" \
  -H "X-Zoom-Client-Id: <your-client-id>" \
  -H "X-Zoom-Client-Secret: <your-client-secret>" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: <session-id-from-initialize>" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "zoom_check_user_email",
      "arguments": {"email": "someone@example.com"}
    }
  }'
```

**Structurally verified** (2026-08-03): MCP handshake (initialize/
initialized), `tools/list` (5 tools, 0 schema errors), `GET /health`,
and 401 credential-gating on `/mcp` all confirmed working against a
locally running instance. A tool call made with a syntactically valid
but fake Account ID/Client ID/Client Secret correctly reached Zoom's
real OAuth endpoint and returned Zoom's own documented error shape
(`HTTP 400 {"reason":"Invalid client_id or client_secret","error":"invalid_client"}`),
confirming the request construction (Basic-auth-encoded client
credentials, `account_credentials` grant, `account_id` param) is
correct per Zoom's own documentation.

## API Reference

- Public, no login required: `https://developers.zoom.us/docs/api/users/`
  (Users Admin API — Create users / Check a user email / Get a user /
  Add group members / List groups, all used here)
- Public, no login required: `https://developers.zoom.us/docs/internal-apps/s2s-oauth/`
  (Server-to-Server OAuth — how to create the app and generate access
  tokens)

## Known Gaps

- **No test S2S OAuth app credentials available yet** — this build has
  not been end-to-end verified against a real Zoom account. Structural
  verification (handshake/tools-list/401 gating/real-OAuth-endpoint
  reachability) is complete; functional verification with real data is
  pending a test Account ID/Client ID/Client Secret with the required
  scopes (`user:write:admin`, `user:read:admin`, `group:read:admin`,
  `group:write:admin`).
- **Scope is exactly the ClickUp task's ask** ("Account creation /
  validation", provisioning group-driven) — Zoom's Users Admin API also
  covers user update/delete, assistants, collaboration devices,
  vanity/PM room settings, contact groups, divisions, and more; those
  are out of scope here.
- **MSPbots has no existing "Zoom" integration configured** (confirmed
  via `web/int/sys/integration/list` — no `ZOOM`/`zoom` entry exists),
  so there was no prior MSPbots interface/param shape to align this
  server's scope against; the tool set here is designed directly from
  the ClickUp task description and Zoom's official API docs.
- `zoom_create_user`'s `action="custCreate"` requires a separate Zoom
  ISV sales agreement per Zoom's own docs — this server does not
  validate that prerequisite, Zoom's API will reject the call if it's
  not met.
