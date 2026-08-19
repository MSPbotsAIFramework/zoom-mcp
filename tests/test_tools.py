"""tools/list snapshot + error-envelope mapping tests.

No network calls: tool enumeration goes through FastMCP's in-process
list_tools(), and the error-code mapping is tested directly against
ZoomError, independent of any real HTTP request.
"""

import pytest

from zoom_mcp.api_client import ZoomError
from zoom_mcp.config import Settings
from zoom_mcp.server import create_mcp_server

EXPECTED_TOOLS = {
    "zoom_list_groups": set(),
    "zoom_create_a_group": set(),
    "zoom_get_a_group": {"group_id"},
    "zoom_update_a_group": {"group_id"},
    "zoom_list_group_members": {"group_id"},
    "zoom_add_group_members": {"group_id"},
    "zoom_delete_a_group_member": {"group_id", "member_id"},
    "zoom_list_users": set(),
    "zoom_create_users": {"action"},
    "zoom_check_a_user_email": {"email"},
    "zoom_get_a_user": {"user_id"},
    "zoom_delete_a_user": {"user_id"},
    "zoom_update_a_user": {"user_id"},
    "zoom_get_user_permissions": {"user_id"},
    "zoom_update_user_status": {"user_id", "action"},
}

READ_ONLY_TOOLS = {
    "zoom_list_groups",
    "zoom_get_a_group",
    "zoom_list_group_members",
    "zoom_list_users",
    "zoom_check_a_user_email",
    "zoom_get_a_user",
    "zoom_get_user_permissions",
}

DESTRUCTIVE_TOOLS = {"zoom_delete_a_group_member", "zoom_delete_a_user"}


@pytest.mark.asyncio
async def test_tools_list_snapshot():
    mcp = create_mcp_server(Settings())
    tools = await mcp.list_tools()
    names = {t.name for t in tools}
    assert names == set(EXPECTED_TOOLS), f"unexpected tool set: {names}"
    assert len(names) <= 20, "tool count should stay within the SOP's ~20 guideline"

    by_name = {t.name: t for t in tools}
    for name, expected_required in EXPECTED_TOOLS.items():
        tool = by_name[name]
        required = set(tool.inputSchema.get("required", []))
        assert required == expected_required, f"{name}: required={required}"

        assert tool.annotations is not None
        if name in READ_ONLY_TOOLS:
            assert tool.annotations.readOnlyHint is True, f"{name}: expected readOnlyHint"
        if name in DESTRUCTIVE_TOOLS:
            assert tool.annotations.destructiveHint is True, f"{name}: expected destructiveHint"

        description = tool.description or ""
        assert len(description) <= 500, f"{name}: description too long ({len(description)} chars)"
        first_line = description.strip().splitlines()[0]
        assert len(first_line) <= 100, f"{name}: first line too long: {first_line!r}"
        assert "API:" not in description, f"{name}: description leaks an implementation detail line"


@pytest.mark.asyncio
async def test_service_instructions_present_and_bounded():
    mcp = create_mcp_server(Settings())
    assert mcp.instructions
    assert len(mcp.instructions) <= 1500


@pytest.mark.parametrize(
    "status_code,expected_code,expected_retryable",
    [
        (0, "upstream_error", True),
        (400, "invalid_argument", False),
        (401, "unauthorized", False),
        (403, "unauthorized", False),
        (404, "not_found", False),
        (422, "invalid_argument", False),
        (429, "rate_limited", True),
        (500, "upstream_error", True),
        (503, "upstream_error", True),
    ],
)
def test_error_envelope_mapping(status_code, expected_code, expected_retryable):
    import json

    err = ZoomError(status_code, "boom")
    envelope = json.loads(err.to_envelope())
    assert envelope["error"]["code"] == expected_code
    assert envelope["error"]["retryable"] is expected_retryable
    assert envelope["error"]["message"] == "boom"
