# zoom-mcp

MCP server for **Zoom**'s Users Admin REST API. Wraps the official
`https://developers.zoom.us/docs/api/users/` spec — Users, Groups, Contact
Groups, and Divisions — driven by PRD-14714's "Account creation /
validation" requirement (onboarding step: account creation and
group-driven provisioning, plus validation). **22 tools**, trimmed down
from an original 71-tool full-API build (2026-08-04) — see Scope below.

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

**22 tools**, trimmed down from an original 71-tool full-API build
(2026-08-04). MSPbots has no existing "Zoom" integration configured
(confirmed via `web/int/sys/integration/list`), so — matching the approach
used for `duo-mcp` elsewhere in this program — "actual usage" was taken
from the original PRD-14714 task's own stated requirement instead:
**account creation and group-driven provisioning, plus validation**. That
maps to:

- **`users` (8 of 35 original)**: `zoom_create_users`,
  `zoom_check_a_user_email` (email-availability validation),
  `zoom_get_a_user`, `zoom_list_users`, `zoom_update_a_user`,
  `zoom_delete_a_user`, `zoom_update_user_status` (activate/deactivate —
  part of provisioning/validation), `zoom_get_user_permissions`
- **`groups` (8 of 21 original)**: `zoom_list_groups`,
  `zoom_create_a_group`, `zoom_get_a_group`, `zoom_update_a_group`,
  `zoom_delete_a_group`, plus membership management (the "group-driven"
  half of provisioning) — `zoom_list_group_members`,
  `zoom_add_group_members`, `zoom_delete_a_group_member`
- **`contact_groups` (4 of 8 original)**: `zoom_list_contact_groups`,
  `zoom_create_a_contact_group`, `zoom_get_a_contact_group`,
  `zoom_add_contact_group_members`
- **`divisions` (2 of 7 original)**: `zoom_list_divisions`,
  `zoom_get_a_division`

Everything else (assistants, collaboration devices, meeting summary
templates, password/profile-picture/presence/scheduler/settings/virtual-
background management on `users`; admins/channels/locked-settings/webinar-
registration/virtual-background on `groups`; remove-members/full CRUD
depth on `contact_groups` and `divisions` — ~49 tools) was removed as
unrelated to account creation/provisioning/validation. If a removed
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
in the Zoom App Marketplace) — grant the full set to use every tool
below: `user:read:admin`, `user:write:admin`, `group:read:admin`,
`group:write:admin`, `contact_group:read:admin`,
`contact_group:write:admin`. (Divisions endpoints ride on the
`user:*:admin` scopes; Zoom does not define separate division scopes.)

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

Tool names are derived from each operation's own summary in Zoom's
OpenAPI spec (e.g. "Check a user email" → `zoom_check_a_user_email`).
The one naming collision — "Upload/Delete Virtual Background files"
exists once for Groups and once for Users — is disambiguated with a
`group_`/`user_` prefix. `dict`/`list[dict]` parameters accept the
vendor's own nested object shape as-is; see the API Reference link
below for the exact sub-field names of each.

| Category | Tool | Description | Method + Path | Params |
|---|---|---|---|---|
| contact_groups | `zoom_add_contact_group_members` | Add contact group members | POST /contacts/groups/{groupId}/members | group_id(required), group_members(optional) |
| contact_groups | `zoom_create_a_contact_group` | Create a contact group | POST /contacts/groups | group_name(optional), group_privacy(optional), description(optional), group_members(optional) |
| contact_groups | `zoom_get_a_contact_group` | Get a contact group | GET /contacts/groups/{groupId} | group_id(required) |
| contact_groups | `zoom_list_contact_groups` | List contact groups | GET /contacts/groups | page_size(required), next_page_token(optional) |
| divisions | `zoom_get_a_division` | Get a division | GET /divisions/{divisionId} | division_id(required) |
| divisions | `zoom_list_divisions` | List divisions | GET /divisions | next_page_token(optional), page_size(required) |
| groups | `zoom_add_group_members` | Add group members | POST /groups/{groupId}/members | group_id(required), members(optional) |
| groups | `zoom_create_a_group` | Create a group | POST /groups | name(optional) |
| groups | `zoom_delete_a_group` | Delete a group | DELETE /groups/{groupId} | group_id(required) |
| groups | `zoom_delete_a_group_member` | Delete a group member | DELETE /groups/{groupId}/members/{memberId} | group_id(required), member_id(required) |
| groups | `zoom_get_a_group` | Get a group | GET /groups/{groupId} | group_id(required) |
| groups | `zoom_list_group_members` | List group members | GET /groups/{groupId}/members | group_id(required), page_size(required), page_number(required), next_page_token(optional) |
| groups | `zoom_list_groups` | List groups | GET /groups | page_size(optional), next_page_token(optional) |
| groups | `zoom_update_a_group` | Update a group | PATCH /groups/{groupId} | group_id(required), name(optional) |
| users | `zoom_check_a_user_email` | Check a user email | GET /users/email | email(required) |
| users | `zoom_create_users` | Create users | POST /users | action(required), user_info(optional) |
| users | `zoom_delete_a_user` | Delete a user | DELETE /users/{userId} | user_id(required), encrypted_email(required), action(required), transfer_email(optional), transfer_meeting(optional), transfer_webinar(optional), transfer_recording(optional), transfer_whiteboard(optional), transfer_clipfiles(optional), transfer_notes(optional), transfer_visitors(optional), transfer_docs(optional), transfer_events(required) |
| users | `zoom_get_a_user` | Get a user | GET /users/{userId} | user_id(required), login_type(optional), encrypted_email(required), search_by_unique_id(optional) |
| users | `zoom_get_user_permissions` | Get user permissions | GET /users/{userId}/permissions | user_id(required) |
| users | `zoom_list_users` | List users | GET /users | status(required), page_size(required), role_id(optional), page_number(optional), include_fields(optional), next_page_token(optional), license(optional) |
| users | `zoom_update_a_user` | Update a user | PATCH /users/{userId} | user_id(required), login_type(optional), remove_tsp_credentials(optional), cms_user_id(optional), company(optional), custom_attributes(optional), dept(optional), first_name(optional), group_id(optional), division_ids(optional), host_key(optional), job_title(optional), cost_center(optional), language(optional), last_name(optional), location(optional), manager(optional), phone_country(optional), phone_number(optional), phone_numbers(optional), pmi(optional), pronouns(optional), pronouns_option(optional), timezone(optional), type(optional), use_pmi(required), vanity_name(optional), display_name(optional), zoom_one_type(optional), plan_united_type(optional), feature(optional), about_me(optional), linkedin_url(optional), license_info_list(optional) |
| users | `zoom_update_user_status` | Update user status | PUT /users/{userId}/status | user_id(required), action(required), transfer_events(optional), transfer_email(optional) |

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

- **Trimmed from 71 to 22 tools on 2026-08-04.** The original build
  covered the full Users Admin API surface per an earlier scope decision
  (justified at the time by there being no MSPbots-existing integration to
  anchor a narrower scope against). A later scope decision cut this back
  to the original PRD-14714 task's actual stated capabilities (account
  creation, group-driven provisioning, validation) plus minimal supporting
  CRUD — see the Scope section above for the exact mapping and the ~49
  removed operations. If a removed operation is needed later, the vendor's
  OpenAPI spec (linked below) still documents it and it can be re-added
  the same way the kept tools were generated.
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
- **3 file-upload endpoints** (`zoom_group_upload_virtual_background_files`,
  `zoom_user_upload_virtual_background_files`,
  `zoom_upload_a_user_s_profile_picture`) take `file_content_base64` +
  `filename` instead of a local file path, since this is a stateless
  HTTP service with no access to the caller's filesystem.
- **`zoom_create_users`' `action="custCreate"`** requires a separate
  Zoom ISV sales agreement per Zoom's own docs — this server does not
  validate that prerequisite, Zoom's API will reject the call if it's
  not met.
