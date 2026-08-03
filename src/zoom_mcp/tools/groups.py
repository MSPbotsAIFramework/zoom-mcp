import json
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..api_client import ZoomClient, ZoomError
from ._common import NO_TOKEN


def register(mcp: FastMCP, client_factory: Callable[[], ZoomClient | None]) -> None:

    @mcp.tool()
    async def zoom_list_groups(page_size: int | None = None, next_page_token: str | None = None) -> str:
        """List groups

API: GET /groups

Args:
    page_size: Optional. The number of records returned in a single API call. The
        maximum is 300.
    next_page_token: Optional. The next page token paginates through a set of large
        results. A next page token is returned whenever the set of available results
        exceeds the current page size. The expiration period for this token is 15
        minutes.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.list_groups(page_size=page_size, next_page_token=next_page_token)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_create_a_group(name: str | None = None) -> str:
        """Create a group

API: POST /groups

Args:
    name: Optional. The group's name.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.create_a_group(name=name)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_get_a_group(group_id: str) -> str:
        """Get a group

API: GET /groups/{groupId}

Args:
    group_id: Required. The group ID. Retrieve by calling the [**List
        groups**](/docs/api-reference/zoom-api/methods#operation/groups) API.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get_a_group(group_id=group_id)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_delete_a_group(group_id: str) -> str:
        """Delete a group

API: DELETE /groups/{groupId}

Args:
    group_id: Required. The group ID. Retrieve by calling the [**List
        groups**](/docs/api-reference/zoom-api/methods#operation/groups) API.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.delete_a_group(group_id=group_id)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_update_a_group(group_id: str, name: str | None = None) -> str:
        """Update a group

API: PATCH /groups/{groupId}

Args:
    group_id: Required. The group ID. Retrieve by calling the [**List
        groups**](/docs/api-reference/zoom-api/methods#operation/groups) API.
    name: Optional. Group name. It must be unique to one account and less than 128
        characters.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.update_a_group(group_id=group_id, name=name)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_list_group_admins(group_id: str, page_size: int = 30, next_page_token: str | None = None) -> str:
        """List group admins

API: GET /groups/{groupId}/admins

Args:
    group_id: Required. The group ID. Retrieve by calling the [**List
        groups**](/docs/api-reference/zoom-api/methods#operation/groups) API.
    page_size: Optional. The number of records returned within a single API call.
    next_page_token: Optional. Use the next page token to paginate through large result
        sets. A next page token is returned whenever the set of available results
        exceeds the current page size. This token's expiration period is 15 minutes.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.list_group_admins(group_id=group_id, page_size=page_size, next_page_token=next_page_token)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_add_group_admins(group_id: str, admins: list[dict] | None = None) -> str:
        """Add group admins

API: POST /groups/{groupId}/admins

Args:
    group_id: Required. The group ID. Retrieve by calling the [**List
        groups**](/docs/api-reference/zoom-api/methods#operation/groups) API.
    admins: Optional. A list of the administrators to add to a group.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.add_group_admins(group_id=group_id, admins=admins)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_delete_a_group_admin(group_id: str, user_id: str) -> str:
        """Delete a group admin

API: DELETE /groups/{groupId}/admins/{userId}

Args:
    group_id: Required. The group ID. Retrieve by calling the [**List
        groups**](/docs/api-reference/zoom-api/methods#operation/groups) API.
    user_id: Required. The user ID or email address of the user. For user-level apps,
        pass the `me` value.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.delete_a_group_admin(group_id=group_id, user_id=user_id)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_list_group_channels(group_id: str) -> str:
        """List group channels

API: GET /groups/{groupId}/channels

Args:
    group_id: Required. The group ID. Retrieve by calling the [**List
        groups**](/docs/api/rest/reference/user/methods/#operation/groups) API.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.list_group_channels(group_id=group_id)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_get_locked_settings(group_id: str, option: str | None = None) -> str:
        """Get locked settings

API: GET /groups/{groupId}/lock_settings

Args:
    group_id: Required. The group's ID.
    option: Optional. Optional query parameters. * `meeting_security` - Use this query
        parameter to view the meeting security settings applied to the user's account.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get_locked_settings(group_id=group_id, option=option)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_update_locked_settings(group_id: str, option: str | None = None) -> str:
        """Update locked settings

API: PATCH /groups/{groupId}/lock_settings

Args:
    group_id: Required. The group's ID.
    option: Optional. Optional query parameters. * `meeting_security` - View the meeting
        security settings applied to the user's account.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.update_locked_settings(group_id=group_id, option=option)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_list_group_members(group_id: str, page_size: int = 30, page_number: int = 1, next_page_token: str | None = None) -> str:
        """List group members

API: GET /groups/{groupId}/members

Args:
    group_id: Required. The group ID. Retrieve by calling the [**List
        groups**](/docs/api-reference/zoom-api/methods#operation/groups) API.
    page_size: Optional. The number of records returned within a single API call.
    page_number: Optional. **Deprecated.** We will no longer support this field in a
        future release. Instead, use the `next_page_token` for pagination.
    next_page_token: Optional. Use the next page token to paginate through large result
        sets. A next page token is returned whenever the set of available results
        exceeds the current page size. This token's expiration period is 15 minutes.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.list_group_members(group_id=group_id, page_size=page_size, page_number=page_number, next_page_token=next_page_token)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_add_group_members(group_id: str, members: list[dict] | None = None) -> str:
        """Add group members

API: POST /groups/{groupId}/members

Args:
    group_id: Required. The group ID. Retrieve by calling the [**List
        groups**](/docs/api-reference/zoom-api/methods#operation/groups) API.
    members: Optional. List of Group members
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.add_group_members(group_id=group_id, members=members)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_delete_a_group_member(group_id: str, member_id: str) -> str:
        """Delete a group member

API: DELETE /groups/{groupId}/members/{memberId}

Args:
    group_id: Required. The group ID. Retrieve by calling the [**List
        groups**](/docs/api-reference/zoom-api/methods#operation/groups) API.
    member_id: Required. The member ID or email address.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.delete_a_group_member(group_id=group_id, member_id=member_id)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_update_a_group_member(group_id: str, member_id: str, action: str, target_group_id: str | None = None) -> str:
        """Update a group member

API: PATCH /groups/{groupId}/members/{memberId}

Args:
    group_id: Required. The group's unique ID. To get this value, use the [**List
        groups**](/docs/api-reference/zoom-api/methods#operation/groups) API. * To set a
        user's primary group, use the `target_group_id` value for this parameter's
        value. * To move a group member from one group to another, use the `groupId` of
        the...
    member_id: Required. The group member's unique ID. To get this value, use the
        [**List group members**](/docs/api-reference/zoom-
        api/methods#operation/groupMembers) API.
    action: Required. The action to perform: * `move` &mdash; Remove the group member
        from one group and move them to a different group. * `set_primary` &mdash; Set
        the user's primary group. One of: ['move', 'set_primary'].
    target_group_id: Optional. The target group's ID. To get this value, use the [**List
        groups**](/docs/api-reference/zoom-api/methods#operation/groups) API. * To set a
        user's primary group, use the designated primary group's `groupId` value. * To
        move a group member from one group to another, use the `groupId` of the...
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.update_a_group_member(group_id=group_id, member_id=member_id, action=action, target_group_id=target_group_id)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_get_a_group_s_settings(group_id: str, option: str | None = None, custom_query_fields: str | None = None) -> str:
        """Get a group's settings

API: GET /groups/{groupId}/settings

Args:
    group_id: Required.
    option: Optional. Optional query parameters. * `meeting_authentication` - View the
        [meeting authentication settings](https://support.zoom.us/hc/en-
        us/articles/360037117472-Authentication-Profiles-for-Meetings-and-Webinars)
        applied to the user's account. * `recording_authentication` - View the
        [recording... One of: ['meeting_authentication', 'recording_authentication',
        'meeting_security'].
    custom_query_fields: Optional. Provide the name of the field to use to filter the
        response. For example, if you provide `host_video` as the value of this field,
        you will get a response similar to this: { `schedule_meeting`: { `host_video`:
        false } } Provide multiple values by separating them with commas, such as...
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get_a_group_s_settings(group_id=group_id, option=option, custom_query_fields=custom_query_fields)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_update_a_group_s_settings(group_id: str, option: str | None = None) -> str:
        """Update a group's settings

API: PATCH /groups/{groupId}/settings

Args:
    group_id: Required. The group's ID.
    option: Optional. Optional query parameters. * `meeting_authentication` - [Meeting
        authentication settings](https://support.zoom.us/hc/en-
        us/articles/360037117472-Authentication-Profiles-for-Meetings-and-Webinars). *
        `recording_authentication` - [Recording authentication... One of:
        ['meeting_authentication', 'recording_authentication', 'meeting_security'].
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.update_a_group_s_settings(group_id=group_id, option=option)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_get_a_group_s_webinar_registration_settings(group_id: str, type: str | None = None) -> str:
        """Get a group's webinar registration settings

API: GET /groups/{groupId}/settings/registration

Args:
    group_id: Required.
    type: Optional. The registration type: * `webinar` &mdash; webinar. One of:
        ['webinar'].
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get_a_group_s_webinar_registration_settings(group_id=group_id, type=type)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_update_a_group_s_webinar_registration_settings(group_id: str, type: str | None = None, options: dict | None = None, questions: list[dict] | None = None, approve_type: int | None = None, custom_questions: list[dict] | None = None) -> str:
        """Update a group's webinar registration settings

API: PATCH /groups/{groupId}/settings/registration

Args:
    group_id: Required. The group ID. Retrieve by calling the List groups API.
    type: Optional. The registration type: * `webinar` &mdash; webinar. One of:
        ['webinar'].
    options: Optional. When participants submit registration, do something.
    questions: Optional. Array of Registrant Questions.
    approve_type: Optional. Approval type for the registration. One of: [0, 1].
    custom_questions: Optional. Array of Registrant Custom Questions
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.update_a_group_s_webinar_registration_settings(group_id=group_id, type=type, options=options, questions=questions, approve_type=approve_type, custom_questions=custom_questions)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_group_upload_virtual_background_files(group_id: str, file_content_base64: str, filename: str) -> str:
        """Upload Virtual Background files

API: POST /groups/{groupId}/settings/virtual_backgrounds

Args:
    group_id: Required. The group ID. To get a group's ID, use the [**List
        groups**](/api-reference/zoom-api/methods#operation/groups) API.

file_content_base64: Required. The file's raw bytes, base64-encoded.
filename: Required. The file name to send with the upload.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.group_upload_virtual_background_files(group_id=group_id, file_content_base64=file_content_base64, filename=filename)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_group_delete_virtual_background_files(group_id: str, file_ids: str | None = None) -> str:
        """Delete Virtual Background files

API: DELETE /groups/{groupId}/settings/virtual_backgrounds

Args:
    group_id: Required. The group ID. To get a group's ID, use the [**List
        groups**](/api-reference/zoom-api/methods#operation/groups) API.
    file_ids: Optional. A comma-separated list of the file IDs to delete.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.group_delete_virtual_background_files(group_id=group_id, file_ids=file_ids)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"
