# zoom-mcp

MCP server for **Zoom**'s Users Admin REST API. Full coverage of the
official `https://developers.zoom.us/docs/api/users/` spec — Users,
Groups, Contact Groups, and Divisions (71 tools, all methods including
writes) — driven by PRD-14714's "Account creation / validation"
requirement (onboarding step: account creation and group-driven
provisioning, plus validation).

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
- All 71 tools were generated mechanically from Zoom's own published
  OpenAPI 3.0 spec (`https://developers.zoom.us/api-hub/users/methods/endpoints.json`,
  the machine-readable source behind the public docs page) — path/query
  parameters and request-body fields are flattened into named function
  arguments; nested object/array-of-object fields (e.g. `user_info`,
  `members`, `feature`) are passed through as a raw `dict`/`list[dict]`
  matching the vendor's own schema shape.

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

| Category | Tool | 功能 | 方法+路径 | 参数 |
|---|---|---|---|---|
| Contact Groups | `zoom_list_contact_groups` | List contact groups | GET /contacts/groups | page_size(可选), next_page_token(可选) |
| Contact Groups | `zoom_create_a_contact_group` | Create a contact group | POST /contacts/groups | group_name(可选), group_privacy(可选), description(可选), group_members(可选) |
| Contact Groups | `zoom_get_a_contact_group` | Get a contact group | GET /contacts/groups/{groupId} | group_id(必填) |
| Contact Groups | `zoom_delete_a_contact_group` | Delete a contact group | DELETE /contacts/groups/{groupId} | group_id(必填) |
| Contact Groups | `zoom_update_a_contact_group` | Update a contact group | PATCH /contacts/groups/{groupId} | group_id(必填), name(可选), privacy(可选), description(可选) |
| Contact Groups | `zoom_list_contact_group_members` | List contact group members | GET /contacts/groups/{groupId}/members | group_id(必填), page_size(可选), next_page_token(可选) |
| Contact Groups | `zoom_add_contact_group_members` | Add contact group members | POST /contacts/groups/{groupId}/members | group_id(必填), group_members(可选) |
| Contact Groups | `zoom_remove_members_in_a_contact_group` | Remove members in a contact group | DELETE /contacts/groups/{groupId}/members | group_id(必填), member_ids(必填) |
| Divisions | `zoom_list_divisions` | List divisions | GET /divisions | next_page_token(可选), page_size(可选) |
| Divisions | `zoom_create_a_division` | Create a division | POST /divisions | division_name(必填), division_description(可选) |
| Divisions | `zoom_get_a_division` | Get a division | GET /divisions/{divisionId} | division_id(必填) |
| Divisions | `zoom_delete_a_division` | Delete a division | DELETE /divisions/{divisionId} | division_id(必填) |
| Divisions | `zoom_update_a_division` | Update a division | PATCH /divisions/{divisionId} | division_id(必填), division_name(可选), division_description(可选) |
| Divisions | `zoom_list_division_members` | List division members | GET /divisions/{divisionId}/users | division_id(必填), next_page_token(可选), page_size(可选) |
| Divisions | `zoom_assign_a_division` | Assign a division | POST /divisions/{divisionId}/users | division_id(必填), users(可选) |
| Groups | `zoom_list_groups` | List groups | GET /groups | page_size(可选), next_page_token(可选) |
| Groups | `zoom_create_a_group` | Create a group | POST /groups | name(可选) |
| Groups | `zoom_get_a_group` | Get a group | GET /groups/{groupId} | group_id(必填) |
| Groups | `zoom_delete_a_group` | Delete a group | DELETE /groups/{groupId} | group_id(必填) |
| Groups | `zoom_update_a_group` | Update a group | PATCH /groups/{groupId} | group_id(必填), name(可选) |
| Groups | `zoom_list_group_admins` | List group admins | GET /groups/{groupId}/admins | group_id(必填), page_size(可选), next_page_token(可选) |
| Groups | `zoom_add_group_admins` | Add group admins | POST /groups/{groupId}/admins | group_id(必填), admins(可选) |
| Groups | `zoom_delete_a_group_admin` | Delete a group admin | DELETE /groups/{groupId}/admins/{userId} | group_id(必填), user_id(必填) |
| Groups | `zoom_list_group_channels` | List group channels | GET /groups/{groupId}/channels | group_id(必填) |
| Groups | `zoom_get_locked_settings` | Get locked settings | GET /groups/{groupId}/lock_settings | group_id(必填), option(可选) |
| Groups | `zoom_update_locked_settings` | Update locked settings | PATCH /groups/{groupId}/lock_settings | group_id(必填), option(可选) |
| Groups | `zoom_list_group_members` | List group members | GET /groups/{groupId}/members | group_id(必填), page_size(可选), page_number(可选), next_page_token(可选) |
| Groups | `zoom_add_group_members` | Add group members | POST /groups/{groupId}/members | group_id(必填), members(可选) |
| Groups | `zoom_delete_a_group_member` | Delete a group member | DELETE /groups/{groupId}/members/{memberId} | group_id(必填), member_id(必填) |
| Groups | `zoom_update_a_group_member` | Update a group member | PATCH /groups/{groupId}/members/{memberId} | group_id(必填), member_id(必填), action(必填), target_group_id(可选) |
| Groups | `zoom_get_a_group_s_settings` | Get a group's settings | GET /groups/{groupId}/settings | group_id(必填), option(可选), custom_query_fields(可选) |
| Groups | `zoom_update_a_group_s_settings` | Update a group's settings | PATCH /groups/{groupId}/settings | group_id(必填), option(可选) |
| Groups | `zoom_get_a_group_s_webinar_registration_settings` | Get a group's webinar registration settings | GET /groups/{groupId}/settings/registration | group_id(必填), type(可选) |
| Groups | `zoom_update_a_group_s_webinar_registration_settings` | Update a group's webinar registration settings | PATCH /groups/{groupId}/settings/registration | group_id(必填), type(可选), options(可选), questions(可选), approve_type(可选), custom_questions(可选) |
| Groups | `zoom_group_upload_virtual_background_files` | Upload Virtual Background files | POST /groups/{groupId}/settings/virtual_backgrounds | group_id(必填), file_content_base64(必填), filename(必填) |
| Groups | `zoom_group_delete_virtual_background_files` | Delete Virtual Background files | DELETE /groups/{groupId}/settings/virtual_backgrounds | group_id(必填), file_ids(可选) |
| Users | `zoom_list_users` | List users | GET /users | status(可选), page_size(可选), role_id(可选), page_number(可选), include_fields(可选), next_page_token(可选), license(可选) |
| Users | `zoom_create_users` | Create users | POST /users | action(必填), user_info(可选) |
| Users | `zoom_check_a_user_email` | Check a user email | GET /users/email | email(必填) |
| Users | `zoom_bulk_update_features_for_users` | Bulk update features for users | POST /users/features | feature_type(必填), feature_value(必填), users(必填), subscription_id(可选), license_info_list(可选) |
| Users | `zoom_get_the_user_s_zak` | Get the user's ZAK | GET /users/me/zak | 无 |
| Users | `zoom_get_user_summary` | Get user summary | GET /users/summary | 无 |
| Users | `zoom_check_a_user_s_pm_room` | Check a user's PM room | GET /users/vanity_name | vanity_name(必填) |
| Users | `zoom_get_a_user` | Get a user | GET /users/{userId} | user_id(必填), login_type(可选), encrypted_email(可选), search_by_unique_id(可选) |
| Users | `zoom_delete_a_user` | Delete a user | DELETE /users/{userId} | user_id(必填), encrypted_email(可选), action(可选), transfer_email(可选), transfer_meeting(可选), transfer_webinar(可选), transfer_recording(可选), transfer_whiteboard(可选), transfer_clipfiles(可选), transfer_notes(可选), transfer_visitors(可选), transfer_docs(可选), transfer_events(可选) |
| Users | `zoom_update_a_user` | Update a user | PATCH /users/{userId} | user_id(必填), login_type(可选), remove_tsp_credentials(可选), cms_user_id(可选), company(可选), custom_attributes(可选), dept(可选), first_name(可选), group_id(可选), division_ids(可选), host_key(可选), job_title(可选), cost_center(可选), language(可选), last_name(可选), location(可选), manager(可选), phone_country(可选), phone_number(可选), phone_numbers(可选), pmi(可选), pronouns(可选), pronouns_option(可选), timezone(可选), type(可选), use_pmi(可选), vanity_name(可选), display_name(可选), zoom_one_type(可选), plan_united_type(可选), feature(可选), about_me(可选), linkedin_url(可选), license_info_list(可选) |
| Users | `zoom_list_user_assistants` | List user assistants | GET /users/{userId}/assistants | user_id(必填) |
| Users | `zoom_add_assistants` | Add assistants | POST /users/{userId}/assistants | user_id(必填), assistants(可选) |
| Users | `zoom_delete_user_assistants` | Delete user assistants | DELETE /users/{userId}/assistants | user_id(必填) |
| Users | `zoom_delete_a_user_assistant` | Delete a user assistant | DELETE /users/{userId}/assistants/{assistantId} | user_id(必填), assistant_id(必填) |
| Users | `zoom_list_a_user_s_collaboration_devices` | List a user's collaboration devices | GET /users/{userId}/collaboration_devices | user_id(必填) |
| Users | `zoom_get_collaboration_device_detail` | Get collaboration device detail | GET /users/{userId}/collaboration_devices/{collaborationDeviceId} | user_id(必填), collaboration_device_id(必填) |
| Users | `zoom_update_a_user_s_email` | Update a user's email | PUT /users/{userId}/email | user_id(必填), email(必填) |
| Users | `zoom_get_meeting_summary_templates` | Get meeting summary templates | GET /users/{userId}/meeting_summary_templates | user_id(必填) |
| Users | `zoom_get_meeting_template_detail` | Get meeting template detail | GET /users/{userId}/meeting_templates/{meetingTemplateId} | user_id(必填), meeting_template_id(必填) |
| Users | `zoom_update_a_user_s_password` | Update a user's password | PUT /users/{userId}/password | user_id(必填), password(必填) |
| Users | `zoom_get_user_permissions` | Get user permissions | GET /users/{userId}/permissions | user_id(必填) |
| Users | `zoom_upload_a_user_s_profile_picture` | Upload a user's profile picture | POST /users/{userId}/picture | user_id(必填), file_content_base64(必填), filename(必填) |
| Users | `zoom_delete_a_user_s_profile_picture` | Delete a user's profile picture | DELETE /users/{userId}/picture | user_id(必填) |
| Users | `zoom_get_a_user_presence_status` | Get a user presence status | GET /users/{userId}/presence_status | user_id(必填) |
| Users | `zoom_update_a_user_s_presence_status` | Update a user's presence status | PUT /users/{userId}/presence_status | user_id(必填) |
| Users | `zoom_list_user_schedulers` | List user schedulers | GET /users/{userId}/schedulers | user_id(必填) |
| Users | `zoom_delete_user_schedulers` | Delete user schedulers | DELETE /users/{userId}/schedulers | user_id(必填) |
| Users | `zoom_delete_a_scheduler` | Delete a scheduler | DELETE /users/{userId}/schedulers/{schedulerId} | user_id(必填), scheduler_id(必填) |
| Users | `zoom_get_user_settings` | Get user settings | GET /users/{userId}/settings | user_id(必填), login_type(可选), option(可选), custom_query_fields(可选) |
| Users | `zoom_update_user_settings` | Update user settings | PATCH /users/{userId}/settings | user_id(必填), option(可选) |
| Users | `zoom_user_upload_virtual_background_files` | Upload Virtual Background files | POST /users/{userId}/settings/virtual_backgrounds | user_id(必填), file_content_base64(必填), filename(必填) |
| Users | `zoom_user_delete_virtual_background_files` | Delete Virtual Background files | DELETE /users/{userId}/settings/virtual_backgrounds | user_id(必填), file_ids(可选) |
| Users | `zoom_update_user_status` | Update user status | PUT /users/{userId}/status | user_id(必填), action(必填), transfer_events(可选), transfer_email(可选) |
| Users | `zoom_get_a_user_s_token` | Get a user's token | GET /users/{userId}/token | user_id(必填), type(可选), ttl(可选), meeting_id(可选) |
| Users | `zoom_revoke_a_user_s_sso_token` | Revoke a user's SSO token | DELETE /users/{userId}/token | user_id(必填) |

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

- **No test S2S OAuth app credentials available yet** — this build has
  not been end-to-end verified against a real Zoom account. Structural
  verification (handshake/tools-list/401 gating/real-OAuth-endpoint
  reachability) is complete; functional verification with real data is
  pending a test Account ID/Client ID/Client Secret with the required
  scopes.
- **MSPbots has no existing "Zoom" integration configured** (confirmed
  via `web/int/sys/integration/list` — no `ZOOM`/`zoom` entry exists),
  so there was no prior MSPbots interface/param shape to align this
  server's scope against; coverage instead matches Zoom's own published
  API surface exactly (71 of 71 operations in the Users API spec).
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
