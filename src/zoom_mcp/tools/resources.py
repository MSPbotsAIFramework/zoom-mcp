import json
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..api_client import ZoomClient, ZoomError
from ._common import NO_TOKEN


def register(mcp: FastMCP, client_factory: Callable[[], ZoomClient | None]) -> None:

    @mcp.tool()
    async def zoom_create_user(
        email: str,
        user_type: int = 1,
        action: str = "create",
        display_name: str | None = None,
        division_ids: list[str] | None = None,
    ) -> str:
        """Add a new user to the Zoom account.

        API: POST /users

        Args:
            email: Required. The new user's email address.
            user_type: Optional. 1 = Basic (default), 2 = Licensed,
                4 = Unassigned without Meetings Basic.
            action: Optional. How the account is provisioned. One of:
                "create" (default) — user gets a confirmation email and
                sets their own password; "autoCreate" — for Enterprise
                accounts with a managed domain; "custCreate" — no
                password, can only host/join via start_url/join_url
                (requires a Zoom ISV agreement); "ssoCreate" — for
                accounts with Pre-provisioning SSO User enabled.
            display_name: Optional. Display name (max 10 Chinese
                characters if used).
            division_ids: Optional. List of Division IDs to assign
                (currently only a single division is supported by Zoom).
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.create_user(
                email=email,
                user_type=user_type,
                action=action,
                display_name=display_name,
                division_ids=division_ids,
            )
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_check_user_email(email: str) -> str:
        """Verify whether an email address is already registered as a Zoom
        user within this account.

        API: GET /users/email

        Note: only detects users who signed up via email within this
        account. Users who joined via SSO/Google/Facebook sign-in are not
        detected even if they are in the same account — the response's
        "existed_email" will be false for them regardless of actual
        registration status.

        Args:
            email: Required. The email address to check.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.check_user_email(email)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_get_user(user_id: str, login_type: int | None = None) -> str:
        """Get a Zoom user's full account details, for validating that a
        specific account exists and inspecting its status/type.

        API: GET /users/{userId}

        Args:
            user_id: Required. The user's user ID or email address.
            login_type: Optional. Required only if the user is inactive
                and login_type otherwise cannot be determined: 0 = Facebook,
                1 = Google, 24 = Apple, 27 = Microsoft, 97 = Mobile phone,
                98 = Password, 100 = SSO.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get_user(user_id, login_type=login_type)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_add_group_member(
        group_id: str, email: str | None = None, user_id: str | None = None
    ) -> str:
        """Add an existing Zoom user to a group, for group-driven account
        provisioning. Provide either email or user_id (not both).

        API: POST /groups/{groupId}/members

        Args:
            group_id: Required. The target group's ID (get one from
                zoom_list_groups).
            email: The user's email address. Ignored if user_id is set.
            user_id: The user's user ID.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.add_group_member(group_id, email=email, user_id=user_id)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_list_groups() -> str:
        """List all groups under the Zoom account, to look up group IDs
        for use with zoom_add_group_member.

        API: GET /groups

        No required parameters.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.list_groups()
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"
