# zoom-mcp

MCP server for **Zoom**'s Users Admin REST API. Wraps the official
`https://developers.zoom.us/docs/api/users/` spec — Users and Groups —
driven by PRD-14714's "Account creation / validation" requirement
(onboarding step: account creation and group-driven provisioning, plus
validation). **15 tools**, trimmed down from an original 71-tool
full-API build (2026-08-04), then trimmed again from 22 to 15
(2026-08-07) — see Scope below.

<div align="center">

## MSPbots Connector

**The MCP Gateway built for MSPs: visible, controlled, and your data stays where it belongs.**

[**Get started at connect.mspbots.ai →**](https://connect.mspbots.ai)

</div>

---

MSPbots Connector gives your AI clients one MCP URL to reach your entire MSP stack (RMM, PSA, documentation, security, finance), and gives you control over who can call which tool and a record of everything that was called.

**Hosted service: [connect.mspbots.ai](https://connect.mspbots.ai)** · Free to use.

### Why Connector

![MSPbots Connector](https://stgoss.mspbots.ai/files/mcp/mspbots-mcp.png)

| | |
|---|---|
| **Visible** | Every tool call is logged: who, which vendor, when. Usage dashboard, CSV export, SIEM streaming. |
| **Controlled** | Role-based, per-tool allowlist. Deny by default. |
| **Protected** | Credentials encrypted per record. AI clients never see your vendor passwords or tokens. |
| **MSP-native** | Built for the MSP stack only: RMM, PSA, documentation, security, finance. |

### Quick start

1. **Sign up** at [connect.mspbots.ai](https://connect.mspbots.ai).
2. **Connect your vendors.** Pick from 150+ connectors and authorize each one on the vendor's own page, or bring your own API keys. No extra vendor accounts needed.
3. **Set access.** Create roles and decide which tools each role may call. Nothing is allowed until you allow it.
4. **Add your MCP URL to your AI client.** Copy the URL from your Connector dashboard into Claude, ChatGPT, Cursor, VS Code, Gemini, Codex, or any MCP-capable client.
5. **Ask your AI to do real work**, and watch every call appear in the audit log.

### Features

**Unified gateway**
- One MCP URL for all your AI clients
- 150+ connectors across the MSP stack
- Custom MCP servers supported, free
- Authorization happens on each vendor's own page; the AI never sees passwords or tokens
- Bring your own credentials: use the vendor API keys you already have
- Multiple accounts per app; connect once, reuse across AI clients
- Tool search: finds the right action for the task
- One sign-in; vendor credentials are injected behind the scenes and OAuth tokens refresh automatically

**Visibility**
- Audit log for every tool call (who, which vendor, when)
- Usage dashboard: call volume, top vendors, error rate, per-user activity
- Export audit logs to CSV, or stream to Loki, Graylog, or LogScale (SIEM)
- Optional recording of tool arguments and result summaries (off by default, enabled per organization)

**Control**
- Per-role, per-tool allowlist, deny by default
- owner / admin / member roles
- SCIM provisioning with Entra ID, Okta, JumpCloud, and Google Workspace

**Security**
- Credentials encrypted one record at a time (AES-256-GCM, per-record key)
- AI clients authenticate with OAuth 2.1 + PKCE
- Vendor responses are scanned for prompt-injection patterns and returned as structured data. This is one layer of defense, not a guarantee against every attack.
- Static egress IP for customer firewall and API allowlisting

### Pricing

**Free.**

Links: [connect.mspbots.ai](https://connect.mspbots.ai) · [mspbots.ai](https://mspbots.ai)

---

## Tool Scope

Trimmed from **22 tools to 15 tools** (2026-08-07). The kept surface is
focused on core user-lifecycle management (create / get / list / update /
delete / status / permissions) plus group membership management —
together the two building blocks needed for typical onboarding and
offboarding automation. Contact-group and division management (6 tools
across `contact_groups.py` and `divisions.py`) were dropped as lower-value
niche capabilities for that use case, along with `zoom_delete_a_group`
(group deletion is a rare, high-risk admin action outside the normal
onboarding/offboarding flow). See the Scope section below for the full
before/after mapping.

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
- All tools were generated mechanically from Zoom's own published
  OpenAPI 3.0 spec (`https://developers.zoom.us/api-hub/users/methods/endpoints.json`,
  the machine-readable source behind the public docs page) — path/query
  parameters and request-body fields are flattened into named function
  arguments; nested object/array-of-object fields (e.g. `user_info`,
  `members`, `feature`) are passed through as a raw `dict`/`list[dict]`
  matching the vendor's own schema shape.

## Scope

**15 tools**, trimmed down from an original 71-tool full-API build
(2026-08-04), by way of an intermediate 22-tool build. MSPbots has no
existing "Zoom" integration configured (confirmed via
`web/int/sys/integration/list`), so — matching the approach used for
`duo-mcp` elsewhere in this program — "actual usage" was taken from the
original PRD-14714 task's own stated requirement instead: **account
creation and group-driven provisioning, plus validation**. That maps to:

- **`users` (8 of 35 original)**: `zoom_create_users`,
  `zoom_check_a_user_email` (email-availability validation),
  `zoom_get_a_user`, `zoom_list_users`, `zoom_update_a_user`,
  `zoom_delete_a_user`, `zoom_update_user_status` (activate/deactivate —
  part of provisioning/validation), `zoom_get_user_permissions`
- **`groups` (7 of 21 original)**: `zoom_list_groups`,
  `zoom_create_a_group`, `zoom_get_a_group`, `zoom_update_a_group`,
  plus membership management (the "group-driven" half of provisioning) —
  `zoom_list_group_members`, `zoom_add_group_members`,
  `zoom_delete_a_group_member`

Everything else (assistants, collaboration devices, meeting summary
templates, password/profile-picture/presence/scheduler/settings/virtual-
background management on `users`; admins/channels/locked-settings/webinar-
registration/virtual-background/`zoom_delete_a_group` on `groups`; all of
`contact_groups` and `divisions` — ~56 tools) was removed as unrelated to
account creation/provisioning/validation, or (in the case of
`zoom_delete_a_group`, contact groups, and divisions) as lower-value/niche
for typical onboarding-offboarding automation use cases. If a removed
operation is needed later, the vendor's OpenAPI spec (linked above) still
documents it and it can be re-added the same way the kept tools were
generated.

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

### HEADER Authorization Parameters

| Header | Type | Required | Default | Allowed values | Description | Example |
|---|---|---|---|---|---|---|
| `X-Zoom-Account-Id` | string | Yes | None | None | Account ID of the Zoom Server-to-Server OAuth app (Zoom App Marketplace -> Manage -> the app -> Basic Information -> App Credentials) | `Ab1CdEfGhIJkLmNoPq2rS` |
| `X-Zoom-Client-Id` | string | Yes | None | None | Client ID of the same S2S OAuth app | `a1B2c3D4e5F6g7H8i9J0` |
| `X-Zoom-Client-Secret` | string | Yes | None | None | Client Secret of the same S2S OAuth app | `k1L2m3N4o5P6q7R8s9T0u1V2` |

Missing any header returns `401`:
```json
{
  "error": "Missing credentials",
  "message": "This server requires the X-Zoom-Account-Id, X-Zoom-Client-Id, X-Zoom-Client-Secret headers",
  "required_headers": ["X-Zoom-Account-Id", "X-Zoom-Client-Id", "X-Zoom-Client-Secret"],
  "optional_headers": []
}
```

Invalid app credentials surface as a structured tool-level error envelope
from the token exchange itself, e.g.:
```json
{"error": {"code": "invalid_argument", "message": "Invalid client_id or client_secret", "retryable": false}}
```

Required scopes on the S2S OAuth app (set on the app's **Scopes** page
in the Zoom App Marketplace) — grant the full set to use every tool
below: `user:read:admin`, `user:write:admin`, `group:read:admin`,
`group:write:admin`.

## Environment Variables

| Variable | Type | Required | Default | Description |
|---|---|---|---|---|
| `MCP_HTTP_PORT` | int | No | `8080` | HTTP listen port |
| `MCP_HTTP_HOST` | string | No | `0.0.0.0` | HTTP listen address |
| `ZOOM_OAUTH_URL` | string | No | `https://zoom.us/oauth/token` | Zoom OAuth token endpoint |
| `ZOOM_API_BASE_URL` | string | No | `https://api.zoom.us/v2` | Zoom REST API base URL |

## MCP Endpoint

- `POST /mcp` — MCP protocol (streamable HTTP transport)
- `GET /health` — health check, returns `{"status": "ok"}` (pure local probe, does not call Zoom)

## Tool List

Tool names are derived from each operation's own summary in Zoom's
OpenAPI spec (e.g. "Check a user email" → `zoom_check_a_user_email`).
The one naming collision — "Upload/Delete Virtual Background files"
exists once for Groups and once for Users — is disambiguated with a
`group_`/`user_` prefix. `dict`/`list[dict]` parameters accept the
vendor's own nested object shape as-is; see the API Reference link
below for the exact sub-field names of each.

| Category | Tool | Description | Method + Path | Params | Annotations |
|---|---|---|---|---|---|
| groups | `zoom_add_group_members` | Add group members | POST /groups/{groupId}/members | group_id(required), members(optional) | — |
| groups | `zoom_create_a_group` | Create a group | POST /groups | name(optional) | — |
| groups | `zoom_delete_a_group_member` | Delete a group member | DELETE /groups/{groupId}/members/{memberId} | group_id(required), member_id(required) | destructive, idempotent |
| groups | `zoom_get_a_group` | Get a group | GET /groups/{groupId} | group_id(required) | readOnly |
| groups | `zoom_list_group_members` | List group members | GET /groups/{groupId}/members | group_id(required), page_size(optional, max 2000), page_number(optional, deprecated), next_page_token(optional) | readOnly |
| groups | `zoom_list_groups` | List groups | GET /groups | page_size(optional, max 300), next_page_token(optional) | readOnly |
| groups | `zoom_update_a_group` | Update a group | PATCH /groups/{groupId} | group_id(required), name(optional) | idempotent |
| users | `zoom_check_a_user_email` | Check a user email | GET /users/email | email(required) | readOnly |
| users | `zoom_create_users` | Create users | POST /users | action(required), user_info(optional) | — |
| users | `zoom_delete_a_user` | Delete a user | DELETE /users/{userId} | user_id(required), encrypted_email(optional), action(optional), transfer_email(optional), transfer_meeting(optional), transfer_webinar(optional), transfer_recording(optional), transfer_whiteboard(optional), transfer_clipfiles(optional), transfer_notes(optional), transfer_visitors(optional), transfer_docs(optional), transfer_events(optional) | destructive, idempotent |
| users | `zoom_get_a_user` | Get a user | GET /users/{userId} | user_id(required), login_type(optional), encrypted_email(optional), search_by_unique_id(optional) | readOnly |
| users | `zoom_get_user_permissions` | Get user permissions | GET /users/{userId}/permissions | user_id(required) | readOnly |
| users | `zoom_list_users` | List users | GET /users | status(optional, default active), page_size(optional, max 2000), role_id(optional), page_number(optional, deprecated), include_fields(optional), next_page_token(optional), license(optional) | readOnly |
| users | `zoom_update_a_user` | Update a user | PATCH /users/{userId} | user_id(required), plus ~30 optional profile/licensing fields (see tool schema) | idempotent |
| users | `zoom_update_user_status` | Update user status | PUT /users/{userId}/status | user_id(required), action(required), transfer_events(optional), transfer_email(optional) | idempotent |

`page_size` maximums above are Zoom's own documented per-endpoint ceilings
(from `https://developers.zoom.us/api-hub/users/methods/endpoints.json`),
clamped server-side rather than left unbounded — they differ per endpoint
(300 for `/groups`, 2000 for `/users` and `/groups/{groupId}/members`), so
each tool clamps against its own real vendor maximum instead of a single
shared constant.

Errors are returned as a structured JSON envelope (not raised as
exceptions), e.g. `{"error": {"code": "not_found", "message": "...",
"retryable": false}}`. `code` is one of: `not_configured`, `unauthorized`,
`not_found`, `invalid_argument`, `rate_limited`, `upstream_error`.

## Test Example

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
      "name": "zoom_check_a_user_email",
      "arguments": {"email": "someone@example.com"}
    }
  }'
```

**Structurally verified** (2026-08-03): MCP handshake (initialize/
initialized), `tools/list` (71 tools, 0 schema errors, 0 name
collisions), `GET /health`, and 401 credential-gating on `/mcp` all
confirmed working against a locally running instance. A tool call made
with a syntactically valid but fake Account ID/Client ID/Client Secret
correctly reached Zoom's real OAuth endpoint and returned Zoom's own
documented error shape
(`HTTP 400 {"reason":"Invalid client_id or client_secret","error":"invalid_client"}`),
confirming the request construction (Basic-auth-encoded client
credentials, `account_credentials` grant, `account_id` param) is
correct per Zoom's own documentation.

**Re-verified after the 22→15 trim** (2026-08-07): MCP handshake,
`tools/list` (15 tools, 0 duplicate names), and `GET /health` confirmed
working against a locally running instance.

## API Reference

- Public, no login required: `https://developers.zoom.us/docs/api/users/`
  (Users Admin API — human-readable docs for all 71 operations covered
  here)
- Public, no login required: `https://developers.zoom.us/api-hub/users/methods/endpoints.json`
  (the machine-readable OpenAPI 3.0 spec this server's tools were
  generated from — the authoritative source for exact nested-object
  field names inside any `dict`/`list[dict]` parameter)
- Public, no login required: `https://developers.zoom.us/docs/internal-apps/s2s-oauth/`
  (Server-to-Server OAuth — how to create the app and generate access
  tokens)

## Known Gaps

- **Trimmed from 71 to 22 tools on 2026-08-04, then from 22 to 15 tools
  on 2026-08-07.** The original build covered the full Users Admin API
  surface per an earlier scope decision (justified at the time by there
  being no MSPbots-existing integration to anchor a narrower scope
  against). A later scope decision cut this back to the original
  PRD-14714 task's actual stated capabilities (account creation,
  group-driven provisioning, validation) plus minimal supporting CRUD,
  landing at 22 tools. The 2026-08-07 pass narrowed this further to core
  user lifecycle (create/get/list/update/delete/status/permissions) and
  group membership management, dropping contact-group management,
  division management, and `zoom_delete_a_group` as lower-value/niche for
  typical onboarding-offboarding automation use cases — see the Scope
  section above for the exact mapping and the removed operations. If a
  removed operation is needed later, the vendor's OpenAPI spec (linked
  below) still documents it and it can be re-added the same way the kept
  tools were generated.
- **No test S2S OAuth app credentials available yet** — this build has
  not been end-to-end verified against a real Zoom account. Structural
  verification (handshake/tools-list/401 gating/real-OAuth-endpoint
  reachability) is complete; functional verification with real data is
  pending a test Account ID/Client ID/Client Secret with the required
  scopes.
- **MSPbots has no existing "Zoom" integration configured** (confirmed
  via `web/int/sys/integration/list` — no `ZOOM`/`zoom` entry exists),
  so there was no prior MSPbots interface/param shape to align this
  server's scope against; see Scope above for how the trim target was
  determined instead.
- **Nested object/array-of-object body fields are passed through as a
  raw `dict`/`list[dict]`** rather than flattened into individual named
  arguments (e.g. `zoom_create_users`' `user_info`, `zoom_add_group_members`'
  `members`) — this matches the flattening convention used across this
  fleet's other large, mechanically-generated vendor-mcps
  (connectsecure-mcp, covedataprotection-mcp, duo-mcp) for complex
  nested structures. Consult the OpenAPI spec link above for each
  dict's exact sub-field names.
- **Some top-level fields Zoom's own spec does not literally mark
  `required` are nonetheless practically required for the call to
  succeed** — e.g. `zoom_create_users`' `user_info` is optional per
  the spec's top-level `required` list (only `action` is marked
  required there), even though omitting it makes user creation
  meaningless. Required/optional markings here follow Zoom's spec
  literally rather than inferring intent, per this fleet's established
  practice of not second-guessing a vendor's documented contract.
- **`zoom_create_users`' `action="custCreate"`** requires a separate
  Zoom ISV sales agreement per Zoom's own docs — this server does not
  validate that prerequisite, Zoom's API will reject the call if it's
  not met.

## Vendor MCP SOP (0818) Compliance Pass — 2026-08-19

Refactored to the stricter `vendor-mcp-development-sop-0818.md`:

- Errors are now a structured JSON envelope (`{"error": {"code", "message",
  "retryable"}}`) instead of ad-hoc `f"Error: {e}"` strings — `code` is one
  of the SOP's fixed vocabulary, mapped from the Zoom API's HTTP status.
- Responses are serialized with `dump_json_capped()` (compact, `ensure_ascii=False`,
  auto-truncates the largest list field past 20,000 chars) instead of
  `json.dumps(..., indent=2)`.
- Tools are annotated with `readOnlyHint` / `destructiveHint` / `idempotentHint`
  (`mcp.types.ToolAnnotations`) per their actual read/write/reversibility
  semantics.
- Docstrings were rewritten to a short summary only; all per-parameter
  documentation (including the previously-embedded `API: GET /xxx` lines)
  moved into `Annotated[T, Field(description=...)]` on each parameter, and a
  service-level `instructions` string was added to `FastMCP(...)`.
- `page_size` is now clamped server-side against Zoom's own documented
  per-endpoint maximum (300 for `/groups`, 2000 for `/users` and
  `/groups/{groupId}/members` — confirmed against Zoom's published OpenAPI
  spec, not assumed from the SOP's generic ≤200 fallback) rather than left
  unbounded.
- `GET /health` now returns exactly `{"status": "ok"}` (previously included
  extra `service`/`transport` fields not called for by the contract).
- `api_client.py` was rewritten around a shared module-level `httpx.AsyncClient`
  with SOP-compliant timeouts (`connect=5.0, read=30.0, write=10.0, pool=5.0`)
  and bounded retry/backoff on `429`/`5xx` (respecting `Retry-After`, capped at
  20s, max 3 retries) — previously each call opened its own short-lived
  client with a single flat 30s/60s timeout and no retry logic. In the
  process, ~50 methods for endpoints no tool ever called (divisions, contact
  groups, and various group/user sub-resources such as virtual-background
  upload, presence status, schedulers, and the profile-picture upload) were
  removed as dead code — they were left over from the original 71-tool
  generation pass and had no caller after the 71→22→15 trims described above.
- `tools/resources.py`, a same-purpose duplicate of the tool-registration
  wiring that only re-exported `groups`/`users`, was removed; `server.py` now
  registers both tool modules directly.
- Checked for the "tool registered under an always-false condition" dead-code
  pattern seen in an earlier repo (cisco-umbrella-mcp) — not present here;
  registration in `server.py` is unconditional.
- Confirmed no environment-variable credential fallback exists anywhere in
  this codebase (`config.py` holds no credential fields; the gateway
  middleware 401s outright if any of the three required headers is missing) —
  this was already compliant with SOP §3.1 before this pass, no change
  needed.
- Added `tests/test_tools.py` (tools/list snapshot incl. annotations and
  description-length assertions, plus error-code-mapping tests) and
  `tests/test_middleware.py` (401-on-missing/partial-header tests plus a
  contextvar-isolation test), per SOP §10's minimal test set. Added
  `pytest`/`pytest-asyncio` as dev dependencies.
