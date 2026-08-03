import base64

import httpx


class ZoomError(Exception):
    def __init__(self, message: str):
        super().__init__(f"Zoom API error: {message}")


class ZoomClient:
    """Async httpx client wrapping Zoom's Users Admin API (Users, Groups,
    Contact Groups, and Divisions endpoints from
    https://developers.zoom.us/docs/api/users/ ).

    Auth is Server-to-Server OAuth (the "account_credentials" grant --
    Zoom's two-legged OAuth for backend automation, no user redirect):

      POST https://zoom.us/oauth/token
        ?grant_type=account_credentials&account_id=...
        Authorization: Basic base64(client_id:client_secret)
      -> {"access_token": "...", "expires_in": 3599, ...}

    The access token is valid for only 1 hour and there is no refresh
    token, so this client re-authenticates fresh on every single call
    rather than caching it across MCP requests, to stay fully stateless.
    """

    def __init__(
        self,
        account_id: str,
        client_id: str,
        client_secret: str,
        oauth_url: str,
        api_base_url: str,
    ):
        self._account_id = account_id
        self._client_id = client_id
        self._client_secret = client_secret
        self._oauth_url = oauth_url
        self._api_base_url = api_base_url.rstrip("/")

    async def _login(self, client: httpx.AsyncClient) -> str:
        basic = base64.b64encode(f"{self._client_id}:{self._client_secret}".encode()).decode()
        try:
            resp = await client.post(
                self._oauth_url,
                params={"grant_type": "account_credentials", "account_id": self._account_id},
                headers={"Authorization": f"Basic {basic}"},
            )
        except httpx.RequestError as e:
            raise ZoomError(f"{e or type(e).__name__} (oauth/token)") from e
        if resp.status_code >= 400:
            raise ZoomError(f"HTTP {resp.status_code} during login: {resp.text}")
        access_token = resp.json().get("access_token")
        if not access_token:
            raise ZoomError(f"login did not return an access_token: {resp.text}")
        return access_token

    def _clean(self, params: dict | None) -> dict:
        if not params:
            return {}
        return {k: v for k, v in params.items() if v is not None}

    async def _call(
        self, method: str, path: str, params: dict | None = None, json_body: dict | None = None
    ) -> object:
        async with httpx.AsyncClient(timeout=30.0) as client:
            token = await self._login(client)
            headers = {"Authorization": f"Bearer {token}"}
            try:
                resp = await client.request(
                    method,
                    f"{self._api_base_url}{path}",
                    headers=headers,
                    params=self._clean(params),
                    json=json_body,
                )
            except httpx.RequestError as e:
                raise ZoomError(f"{e or type(e).__name__} (path={path})") from e
            if resp.status_code >= 400:
                raise ZoomError(f"HTTP {resp.status_code} calling {path}: {resp.text}")
            if not resp.content:
                return {}
            return resp.json()

    async def _call_multipart(
        self, method: str, path: str, field_name: str, file_content_base64: str, filename: str
    ) -> object:
        content = base64.b64decode(file_content_base64)
        async with httpx.AsyncClient(timeout=60.0) as client:
            token = await self._login(client)
            headers = {"Authorization": f"Bearer {token}"}
            files = {field_name: (filename, content)}
            try:
                resp = await client.request(
                    method, f"{self._api_base_url}{path}", headers=headers, files=files
                )
            except httpx.RequestError as e:
                raise ZoomError(f"{e or type(e).__name__} (path={path})") from e
            if resp.status_code >= 400:
                raise ZoomError(f"HTTP {resp.status_code} calling {path}: {resp.text}")
            if not resp.content:
                return {}
            return resp.json()

    async def list_contact_groups(self, page_size: int = 10, next_page_token: str | None = None) -> object:
        """List contact groups

API: GET /contacts/groups

Args:
    page_size: Optional. The number of records returned with a single API call.
    next_page_token: Optional. The next page token is used to paginate through large
        result sets. A next page token will be returned whenever the set of available
        results exceeds the current page size. The expiration period for this token is
        15 minutes.
        """
        return await self._call("GET", f"/contacts/groups", params=self._clean({"page_size": page_size, "next_page_token": next_page_token}), json_body=None)

    async def create_a_contact_group(self, group_name: str | None = None, group_privacy: int | None = None, description: str | None = None, group_members: list[dict] | None = None) -> object:
        """Create a contact group

API: POST /contacts/groups

Args:
    group_name: Optional. The contact group's name.
    group_privacy: Optional. Contact group privacy configuration: `1` - Visible to
        anyone, searchable by anyone. `2` - Visible to members only, searchable by
        anyone. `3` - Visible to members only, searchable by members only. One of: [1,
        2, 3].
    description: Optional. The group description.
    group_members: Optional.
        """
        return await self._call("POST", f"/contacts/groups", params=None, json_body=self._clean({"group_name": group_name, "group_privacy": group_privacy, "description": description, "group_members": group_members}))

    async def get_a_contact_group(self, group_id: str) -> object:
        """Get a contact group

API: GET /contacts/groups/{groupId}

Args:
    group_id: Required. The contact group ID. Retrieve by calling the [**List contact
        groups**](/docs/api-reference/zoom-api/methods#operation/contactGroups) API.
        """
        return await self._call("GET", f"/contacts/groups/{group_id}", params=None, json_body=None)

    async def delete_a_contact_group(self, group_id: str) -> object:
        """Delete a contact group

API: DELETE /contacts/groups/{groupId}

Args:
    group_id: Required. The contact group ID. Retrieve by calling the [**List contact
        groups**](/docs/api-reference/zoom-api/methods#operation/contactGroups) API.
        """
        return await self._call("DELETE", f"/contacts/groups/{group_id}", params=None, json_body=None)

    async def update_a_contact_group(self, group_id: str, name: str | None = None, privacy: int | None = None, description: str | None = None) -> object:
        """Update a contact group

API: PATCH /contacts/groups/{groupId}

Args:
    group_id: Required. The contact group ID. Retrieve by calling the [**List contact
        groups**](/docs/api-reference/zoom-api/methods#operation/contactGroups) API.
    name: Optional. The contact group's name.
    privacy: Optional. Contact group privacy configuration: `1` - Visible to anyone,
        searchable by anyone. `2` - Visible to members only, searchable by anyone. `3` -
        Visible to members only, searchable by members only. One of: [1, 2, 3].
    description: Optional. The group description.
        """
        return await self._call("PATCH", f"/contacts/groups/{group_id}", params=None, json_body=self._clean({"name": name, "privacy": privacy, "description": description}))

    async def list_contact_group_members(self, group_id: str, page_size: int = 10, next_page_token: str | None = None) -> object:
        """List contact group members

API: GET /contacts/groups/{groupId}/members

Args:
    group_id: Required. The group ID.
    page_size: Optional. The number of records returned with a single API call.
    next_page_token: Optional. The next page token is used to paginate through large
        result sets. A next page token will be returned whenever the set of available
        results exceeds the current page size. The expiration period for this token is
        15 minutes.
        """
        return await self._call("GET", f"/contacts/groups/{group_id}/members", params=self._clean({"page_size": page_size, "next_page_token": next_page_token}), json_body=None)

    async def add_contact_group_members(self, group_id: str, group_members: list[dict] | None = None) -> object:
        """Add contact group members

API: POST /contacts/groups/{groupId}/members

Args:
    group_id: Required. The contact group ID. Retrieve by calling the List contact
        groups API.
    group_members: Optional. Group members array
        """
        return await self._call("POST", f"/contacts/groups/{group_id}/members", params=None, json_body=self._clean({"group_members": group_members}))

    async def remove_members_in_a_contact_group(self, group_id: str, member_ids: str) -> object:
        """Remove members in a contact group

API: DELETE /contacts/groups/{groupId}/members

Args:
    group_id: Required. The contact group ID. Retrieve by calling the List contact
        groups API.
    member_ids: Required. The member's ID in a contact group. Use commas (,) to separate
        a maximum of 20 ids. Can be retrieved by calling the [**List contact
        groups**](/docs/api-reference/zoom-api/methods#operation/contactGroupMembers)
        API.
        """
        return await self._call("DELETE", f"/contacts/groups/{group_id}/members", params=self._clean({"member_ids": member_ids}), json_body=None)

    async def list_divisions(self, next_page_token: str | None = None, page_size: int = 30) -> object:
        """List divisions

API: GET /divisions

Args:
    next_page_token: Optional. Use the next page token to paginate through a large set
        of results. It returns whenever the set of available results exceeds the current
        page size. This token's expiration period is 15 minutes.
    page_size: Optional. The number of records returned within a single API call.
        """
        return await self._call("GET", f"/divisions", params=self._clean({"next_page_token": next_page_token, "page_size": page_size}), json_body=None)

    async def create_a_division(self, division_name: str, division_description: str | None = None) -> object:
        """Create a division

API: POST /divisions

Args:
    division_name: Required. The division's name.
    division_description: Optional. The division's description.
        """
        return await self._call("POST", f"/divisions", params=None, json_body=self._clean({"division_name": division_name, "division_description": division_description}))

    async def get_a_division(self, division_id: str) -> object:
        """Get a division

API: GET /divisions/{divisionId}

Args:
    division_id: Required. The division's id
        """
        return await self._call("GET", f"/divisions/{division_id}", params=None, json_body=None)

    async def delete_a_division(self, division_id: str) -> object:
        """Delete a division

API: DELETE /divisions/{divisionId}

Args:
    division_id: Required. The division's ID.
        """
        return await self._call("DELETE", f"/divisions/{division_id}", params=None, json_body=None)

    async def update_a_division(self, division_id: str, division_name: str | None = None, division_description: str | None = None) -> object:
        """Update a division

API: PATCH /divisions/{divisionId}

Args:
    division_id: Required. The division's ID.
    division_name: Optional. The division's name.
    division_description: Optional. The division's description.
        """
        return await self._call("PATCH", f"/divisions/{division_id}", params=None, json_body=self._clean({"division_name": division_name, "division_description": division_description}))

    async def list_division_members(self, division_id: str, next_page_token: str | None = None, page_size: int = 30) -> object:
        """List division members

API: GET /divisions/{divisionId}/users

Args:
    division_id: Required. The division's ID.
    next_page_token: Optional. Use the next page token to paginate through a large set
        of results. It returns whenever the set of available results exceeds the current
        page size. This token's expiration period is 15 minutes.
    page_size: Optional. The number of records returned within a single API call.
        """
        return await self._call("GET", f"/divisions/{division_id}/users", params=self._clean({"next_page_token": next_page_token, "page_size": page_size}), json_body=None)

    async def assign_a_division(self, division_id: str, users: list[dict] | None = None) -> object:
        """Assign a division

API: POST /divisions/{divisionId}/users

Args:
    division_id: Required. The division's ID.
    users: Optional. Array of userId/user email of users to whom you would like to
        assign this division. Up to 30 users can be assigned a division at once.
        """
        return await self._call("POST", f"/divisions/{division_id}/users", params=None, json_body=self._clean({"users": users}))

    async def list_groups(self, page_size: int | None = None, next_page_token: str | None = None) -> object:
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
        return await self._call("GET", f"/groups", params=self._clean({"page_size": page_size, "next_page_token": next_page_token}), json_body=None)

    async def create_a_group(self, name: str | None = None) -> object:
        """Create a group

API: POST /groups

Args:
    name: Optional. The group's name.
        """
        return await self._call("POST", f"/groups", params=None, json_body=self._clean({"name": name}))

    async def get_a_group(self, group_id: str) -> object:
        """Get a group

API: GET /groups/{groupId}

Args:
    group_id: Required. The group ID. Retrieve by calling the [**List
        groups**](/docs/api-reference/zoom-api/methods#operation/groups) API.
        """
        return await self._call("GET", f"/groups/{group_id}", params=None, json_body=None)

    async def delete_a_group(self, group_id: str) -> object:
        """Delete a group

API: DELETE /groups/{groupId}

Args:
    group_id: Required. The group ID. Retrieve by calling the [**List
        groups**](/docs/api-reference/zoom-api/methods#operation/groups) API.
        """
        return await self._call("DELETE", f"/groups/{group_id}", params=None, json_body=None)

    async def update_a_group(self, group_id: str, name: str | None = None) -> object:
        """Update a group

API: PATCH /groups/{groupId}

Args:
    group_id: Required. The group ID. Retrieve by calling the [**List
        groups**](/docs/api-reference/zoom-api/methods#operation/groups) API.
    name: Optional. Group name. It must be unique to one account and less than 128
        characters.
        """
        return await self._call("PATCH", f"/groups/{group_id}", params=None, json_body=self._clean({"name": name}))

    async def list_group_admins(self, group_id: str, page_size: int = 30, next_page_token: str | None = None) -> object:
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
        return await self._call("GET", f"/groups/{group_id}/admins", params=self._clean({"page_size": page_size, "next_page_token": next_page_token}), json_body=None)

    async def add_group_admins(self, group_id: str, admins: list[dict] | None = None) -> object:
        """Add group admins

API: POST /groups/{groupId}/admins

Args:
    group_id: Required. The group ID. Retrieve by calling the [**List
        groups**](/docs/api-reference/zoom-api/methods#operation/groups) API.
    admins: Optional. A list of the administrators to add to a group.
        """
        return await self._call("POST", f"/groups/{group_id}/admins", params=None, json_body=self._clean({"admins": admins}))

    async def delete_a_group_admin(self, group_id: str, user_id: str) -> object:
        """Delete a group admin

API: DELETE /groups/{groupId}/admins/{userId}

Args:
    group_id: Required. The group ID. Retrieve by calling the [**List
        groups**](/docs/api-reference/zoom-api/methods#operation/groups) API.
    user_id: Required. The user ID or email address of the user. For user-level apps,
        pass the `me` value.
        """
        return await self._call("DELETE", f"/groups/{group_id}/admins/{user_id}", params=None, json_body=None)

    async def list_group_channels(self, group_id: str) -> object:
        """List group channels

API: GET /groups/{groupId}/channels

Args:
    group_id: Required. The group ID. Retrieve by calling the [**List
        groups**](/docs/api/rest/reference/user/methods/#operation/groups) API.
        """
        return await self._call("GET", f"/groups/{group_id}/channels", params=None, json_body=None)

    async def get_locked_settings(self, group_id: str, option: str | None = None) -> object:
        """Get locked settings

API: GET /groups/{groupId}/lock_settings

Args:
    group_id: Required. The group's ID.
    option: Optional. Optional query parameters. * `meeting_security` - Use this query
        parameter to view the meeting security settings applied to the user's account.
        """
        return await self._call("GET", f"/groups/{group_id}/lock_settings", params=self._clean({"option": option}), json_body=None)

    async def update_locked_settings(self, group_id: str, option: str | None = None) -> object:
        """Update locked settings

API: PATCH /groups/{groupId}/lock_settings

Args:
    group_id: Required. The group's ID.
    option: Optional. Optional query parameters. * `meeting_security` - View the meeting
        security settings applied to the user's account.
        """
        return await self._call("PATCH", f"/groups/{group_id}/lock_settings", params=self._clean({"option": option}), json_body={})

    async def list_group_members(self, group_id: str, page_size: int = 30, page_number: int = 1, next_page_token: str | None = None) -> object:
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
        return await self._call("GET", f"/groups/{group_id}/members", params=self._clean({"page_size": page_size, "page_number": page_number, "next_page_token": next_page_token}), json_body=None)

    async def add_group_members(self, group_id: str, members: list[dict] | None = None) -> object:
        """Add group members

API: POST /groups/{groupId}/members

Args:
    group_id: Required. The group ID. Retrieve by calling the [**List
        groups**](/docs/api-reference/zoom-api/methods#operation/groups) API.
    members: Optional. List of Group members
        """
        return await self._call("POST", f"/groups/{group_id}/members", params=None, json_body=self._clean({"members": members}))

    async def delete_a_group_member(self, group_id: str, member_id: str) -> object:
        """Delete a group member

API: DELETE /groups/{groupId}/members/{memberId}

Args:
    group_id: Required. The group ID. Retrieve by calling the [**List
        groups**](/docs/api-reference/zoom-api/methods#operation/groups) API.
    member_id: Required. The member ID or email address.
        """
        return await self._call("DELETE", f"/groups/{group_id}/members/{member_id}", params=None, json_body=None)

    async def update_a_group_member(self, group_id: str, member_id: str, action: str, target_group_id: str | None = None) -> object:
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
        return await self._call("PATCH", f"/groups/{group_id}/members/{member_id}", params=None, json_body=self._clean({"action": action, "target_group_id": target_group_id}))

    async def get_a_group_s_settings(self, group_id: str, option: str | None = None, custom_query_fields: str | None = None) -> object:
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
        return await self._call("GET", f"/groups/{group_id}/settings", params=self._clean({"option": option, "custom_query_fields": custom_query_fields}), json_body=None)

    async def update_a_group_s_settings(self, group_id: str, option: str | None = None) -> object:
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
        return await self._call("PATCH", f"/groups/{group_id}/settings", params=self._clean({"option": option}), json_body={})

    async def get_a_group_s_webinar_registration_settings(self, group_id: str, type: str | None = None) -> object:
        """Get a group's webinar registration settings

API: GET /groups/{groupId}/settings/registration

Args:
    group_id: Required.
    type: Optional. The registration type: * `webinar` &mdash; webinar. One of:
        ['webinar'].
        """
        return await self._call("GET", f"/groups/{group_id}/settings/registration", params=self._clean({"type": type}), json_body=None)

    async def update_a_group_s_webinar_registration_settings(self, group_id: str, type: str | None = None, options: dict | None = None, questions: list[dict] | None = None, approve_type: int | None = None, custom_questions: list[dict] | None = None) -> object:
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
        return await self._call("PATCH", f"/groups/{group_id}/settings/registration", params=self._clean({"type": type}), json_body=self._clean({"options": options, "questions": questions, "approve_type": approve_type, "custom_questions": custom_questions}))

    async def group_upload_virtual_background_files(self, group_id: str, file_content_base64: str, filename: str) -> object:
        """Upload Virtual Background files

API: POST /groups/{groupId}/settings/virtual_backgrounds

Args:
    group_id: Required. The group ID. To get a group's ID, use the [**List
        groups**](/api-reference/zoom-api/methods#operation/groups) API.

file_content_base64: Required. The file's raw bytes, base64-encoded.
filename: Required. The file name to send with the upload.
        """
        return await self._call_multipart(
            "POST", f"/groups/{group_id}/settings/virtual_backgrounds", field_name="file",
            file_content_base64=file_content_base64, filename=filename,
        )

    async def group_delete_virtual_background_files(self, group_id: str, file_ids: str | None = None) -> object:
        """Delete Virtual Background files

API: DELETE /groups/{groupId}/settings/virtual_backgrounds

Args:
    group_id: Required. The group ID. To get a group's ID, use the [**List
        groups**](/api-reference/zoom-api/methods#operation/groups) API.
    file_ids: Optional. A comma-separated list of the file IDs to delete.
        """
        return await self._call("DELETE", f"/groups/{group_id}/settings/virtual_backgrounds", params=self._clean({"file_ids": file_ids}), json_body=None)

    async def list_users(self, status: str = "active", page_size: int = 30, role_id: str | None = None, page_number: str | None = None, include_fields: str | None = None, next_page_token: str | None = None, license: str | None = None) -> object:
        """List users

API: GET /users

Args:
    status: Optional. The user's status. * `active` - The user exists on the account. *
        `inactive` - The user has been deactivated. * `pending` - The user exists on the
        account, but has not activated their account. See [Managing users](https://suppo
        rt.zoom.com/hc/en/article?id=zm_kb&sysparm_article=KB0061789) for... One of:
        ['active', 'inactive', 'pending'].
    page_size: Optional. The number of records returned within a single API call.
    role_id: Optional. The role's unique ID. Use this parameter to filter the response
        by a specific role. You can use the [**List
        roles**](/docs/api/accounts/#tag/roles/GET/roles) API to get a role's unique ID
        value.
    page_number: Optional. The page number of the current page in the returned records.
        We will no longer support this field in a future release. Instead, use the
        next_page_token for pagination.
    include_fields: Optional. This parameter displays one of the following attributes in
        the API call's response: * `custom_attributes` &mdash; Return the user's custom
        attributes. * `host_key` &mdash; Return the user's [host
        key](https://support.zoom.com/hc/en/article?id=zm_kb&sysparm_article=KB0067063).
        One of: ['custom_attributes', 'host_key'].
    next_page_token: Optional. The next page token paginates through a large set of
        results. It returns whenever the set of available results exceeds the current
        page size. The expiration period for this token is 15 minutes.
    license: Optional. The user's license. Filter the response by a specific license.
        One of: ['zoom_workforce_management', 'zoom_compliance_management',
        'zoom_compliance_manager_for_contact_center'].
        """
        return await self._call("GET", f"/users", params=self._clean({"status": status, "page_size": page_size, "role_id": role_id, "page_number": page_number, "include_fields": include_fields, "next_page_token": next_page_token, "license": license}), json_body=None)

    async def create_users(self, action: str, user_info: dict | None = None) -> object:
        """Create users

API: POST /users

Args:
    action: Required. The action to take to create the new user. * `create` - The user
        receives an email from Zoom containing a confirmation link. The user must then
        use the link to activate their Zoom account. The user can then set or change
        their password. * `autoCreate` - This action is for Enterprise customers with...
        One of: ['create', 'autoCreate', 'custCreate', 'ssoCreate'].
    user_info: Optional.
        """
        return await self._call("POST", f"/users", params=None, json_body=self._clean({"action": action, "user_info": user_info}))

    async def check_a_user_email(self, email: str) -> object:
        """Check a user email

API: GET /users/email

Args:
    email: Required. The email address to be verified.
        """
        return await self._call("GET", f"/users/email", params=self._clean({"email": email}), json_body=None)

    async def bulk_update_features_for_users(self, feature_type: str, feature_value: str, users: list[dict], subscription_id: str | None = None, license_info_list: list[dict] | None = None) -> object:
        """Bulk update features for users

API: POST /users/features

Args:
    feature_type: Required. The feature type to update. One of: ['user_type',
        'concurrent_meeting', 'large_meeting', 'webinar', 'zoom_events',
        'zoom_whiteboard', 'plan_united_type', 'zoom_one_type', 'zoom_iq_for_sales',
        'zoom_revenue_accelerator', 'zoom_clips_plus'].
    feature_value: Required. The feature value to update. The value you can pass depends
        on the 'feature_type' field. **user_type:** * `1` - Basic * `2` - Licensed *
        <del>`99` - None. This can only be set with `ssoCreate`. </del>
        **concurrent_meeting:** * `Basic` * `Plus` * `None`. **large_meeting:** * `1` -
        100 capacity *...
    users: Required. The users' information to update.
    subscription_id: Optional. The subscription ID associated with the corresponding
        license. For accounts with duplicate subscription IDs, when zoom_one_type is 0,
        this parameter represents the subscription ID that requires the allocation of a
        meeting license.
    license_info_list: Optional. A list of license information used to specify the
        appropriate license type, license option, and license subscription reference ID
        or name during user creation.
        """
        return await self._call("POST", f"/users/features", params=None, json_body=self._clean({"feature_type": feature_type, "feature_value": feature_value, "users": users, "subscription_id": subscription_id, "license_info_list": license_info_list}))

    async def get_the_user_s_zak(self) -> object:
        """Get the user's ZAK

API: GET /users/me/zak

        """
        return await self._call("GET", f"/users/me/zak", params=None, json_body=None)

    async def get_user_summary(self) -> object:
        """Get user summary

API: GET /users/summary

        """
        return await self._call("GET", f"/users/summary", params=None, json_body=None)

    async def check_a_user_s_pm_room(self, vanity_name: str) -> object:
        """Check a user's PM room

API: GET /users/vanity_name

Args:
    vanity_name: Required. Personal meeting room name.
        """
        return await self._call("GET", f"/users/vanity_name", params=self._clean({"vanity_name": vanity_name}), json_body=None)

    async def get_a_user(self, user_id: str, login_type: int | None = None, encrypted_email: bool = False, search_by_unique_id: bool | None = None) -> object:
        """Get a user

API: GET /users/{userId}

Args:
    user_id: Required. The user's user ID or email address. For user-level apps, pass
        the `me` value.
    login_type: Optional. The user's login method. * `0` - Facebook OAuth * `1` - Google
        OAuth. * `24` - Apple OAuth. * `27` - Microsoft OAuth. * `97` - Mobile device. *
        `98` - RingCentral OAuth. * `99` - API user. * `100` - Zoom Work email. * `101`
        - Single Sign-On (SSO). These login methods are only available in China. *...
        One of: [0, 1, 11, 21, 23, 24, 27, 97, 98, 99, 100, 101].
    encrypted_email: Optional. Whether the email address passed for the `userId` value
        is an encrypted email address. * `true` - The email address is encrypted. *
        `false` - The email address is not encrypted. If you do not query this
        parameter, this value defaults to null (`false`).
    search_by_unique_id: Optional. Whether the queried `userId` value is an employee
        unique ID. * `true` - The queried ID is an employee's unique ID. * `false` - The
        queried ID is not an employee's unique ID. This value defaults to `false`
        (null).
        """
        return await self._call("GET", f"/users/{user_id}", params=self._clean({"login_type": login_type, "encrypted_email": encrypted_email, "search_by_unique_id": search_by_unique_id}), json_body=None)

    async def delete_a_user(self, user_id: str, encrypted_email: bool = False, action: str = "disassociate", transfer_email: str | None = None, transfer_meeting: bool | None = None, transfer_webinar: bool | None = None, transfer_recording: bool | None = None, transfer_whiteboard: bool | None = None, transfer_clipfiles: bool | None = None, transfer_notes: bool | None = None, transfer_visitors: bool | None = None, transfer_docs: bool | None = None, transfer_events: bool = True) -> object:
        """Delete a user

API: DELETE /users/{userId}

Args:
    user_id: Required. The user's user ID or email address. For user-level apps, pass
        the `me` value.
    encrypted_email: Optional. Whether the email address passed for the `userId` value
        is an encrypted email address. * `true` - The email address is encrypted. *
        `false` - The email address is not encrypted. If you do not query this
        parameter, this value defaults to null (`false`).
    action: Optional. Delete action options. `disassociate` - Disassociate a user.
        `delete`- Permanently delete a user. Note: To delete pending user in the
        account, use `disassociate` One of: ['disassociate', 'delete'].
    transfer_email: Optional. Transfer email. This field is **required** if the user has
        Zoom Events/Sessions feature. After you delete or disassociate the user, the
        user's hub assets on Zoom Events site will be transferred to the target user.
        For detailed behavior and requirements, refer to the `transfer_events` field...
    transfer_meeting: Optional. Transfer meeting.
    transfer_webinar: Optional. Transfer webinar.
    transfer_recording: Optional. Transfer recording.
    transfer_whiteboard: Optional. When deleting a user, whether to transfer all their
        [Zoom Whiteboard](https://support.zoom.us/hc/en-us/articles/4410916881421) data
        to another user.
    transfer_clipfiles: Optional. Transfer clip files.
    transfer_notes: Optional. Transfer notes.
    transfer_visitors: Optional. Transfer visitors.
    transfer_docs: Optional. Transfer docs.
    transfer_events: Optional. Indicates whether to transfer Zoom Events. When
        `transfer_events` is set to `true`, the `transfer_email` field is required. Upon
        user deletion or disassociation, the user’s Zoom Events hub assets will be
        transferred to the specified target user. When `transfer_events` is set to
        `false`, the...
        """
        return await self._call("DELETE", f"/users/{user_id}", params=self._clean({"encrypted_email": encrypted_email, "action": action, "transfer_email": transfer_email, "transfer_meeting": transfer_meeting, "transfer_webinar": transfer_webinar, "transfer_recording": transfer_recording, "transfer_whiteboard": transfer_whiteboard, "transfer_clipfiles": transfer_clipfiles, "transfer_notes": transfer_notes, "transfer_visitors": transfer_visitors, "transfer_docs": transfer_docs, "transfer_events": transfer_events}), json_body=None)

    async def update_a_user(self, user_id: str, login_type: int | None = None, remove_tsp_credentials: bool | None = None, cms_user_id: str | None = None, company: str | None = None, custom_attributes: list[dict] | None = None, dept: str | None = None, first_name: str | None = None, group_id: str | None = None, division_ids: list[str] | None = None, host_key: str | None = None, job_title: str | None = None, cost_center: str | None = None, language: str | None = None, last_name: str | None = None, location: str | None = None, manager: str | None = None, phone_country: str | None = None, phone_number: str | None = None, phone_numbers: list[dict] | None = None, pmi: int | None = None, pronouns: str | None = None, pronouns_option: int | None = None, timezone: str | None = None, type: int | None = None, use_pmi: bool = False, vanity_name: str | None = None, display_name: str | None = None, zoom_one_type: int | None = None, plan_united_type: str | None = None, feature: dict | None = None, about_me: str | None = None, linkedin_url: str | None = None, license_info_list: list[dict] | None = None) -> object:
        """Update a user

API: PATCH /users/{userId}

Args:
    user_id: Required. The user ID or email address. For user-level apps, pass the `me`
        value.
    login_type: Optional. The user's login method. * `0` - Facebook OAuth. * `1` -
        Google OAuth. * `24` - Apple OAuth. * `27` - Microsoft OAuth. * `97` - Mobile
        device. * `98` - RingCentral OAuth. * `99` - API user. * `100` - Zoom Work
        email. * `101` - Single Sign-On (SSO). These login methods are only available in
        China. *... One of: [0, 1, 11, 21, 23, 24, 27, 97, 98, 99, 100, 101].
    remove_tsp_credentials: Optional. Whether to remove the user's TSP credentials. *
        `true` - The queried ID is an employee's unique ID. * `false` - The queried ID
        is not an employee's unique ID. This value defaults to `false` (null).
    cms_user_id: Optional. The Kaltura user ID.
    company: Optional. The user's company.
    custom_attributes: Optional. The user's assigned custom attributes.
    dept: Optional. The user's assigned department.
    first_name: Optional. The user's first name. This value cannot contain more than
        five Chinese characters.
    group_id: Optional. This field provides the unique identifier of the group that you
        would like to add a [pending user](https://support.zoom.us/hc/en-
        us/articles/201363183-Managing-users#h_13c87a2a-ecd6-40ad-be61-a9935e660edb) to.
        Retrieve the value of this field from the [**List...
    division_ids: Optional. List of division IDs to be updated. Currently only a single
        division is supported.
    host_key: Optional. The user's host key.
    job_title: Optional. The user's job title.
    cost_center: Optional. The user's cost center.
    language: Optional. The user's language.
    last_name: Optional. The user's last name. This value cannot contain more than five
        Chinese characters.
    location: Optional. The user's location.
    manager: Optional. The user's assigned manager. To set a manager, provide the
        manager’s email address or display name within the same account.
    phone_country: Optional. **Note** This field has been **deprecated** and will not be
        supported in the future. Use the `country` field of the `phone_numbers` object
        to select the phone number country. The user's phone number [country...
    phone_number: Optional. **Note** This field has been **deprecated** and will not be
        supported in the future. Instead, use the `phone_numbers` field to assign phone
        numbers to a user. The user's phone number. To update a phone number, you must
        also provide the `phone_country` field.
    phone_numbers: Optional. The information about the user's assigned phone numbers.
    pmi: Optional. The user's [personal meeting ID
        (PMI)](https://developers.zoom.us/docs/api/rest/using-zoom-apis/#understanding-
        personal-meeting-id-pmi).
    pronouns: Optional. The user's pronouns.
    pronouns_option: Optional. The user's display pronouns setting. * `1` - Ask the user
        every time they join meetings and webinars. * `2` - Always display pronouns in
        meetings and webinars. * `3` - Do not display pronouns in meetings and webinars.
        One of: [1, 2, 3].
    timezone: Optional. The user's
        [timezone](https://developers.zoom.us/docs/api/rest/other-
        references/abbreviation-lists/#timezones)
    type: Optional. The type of [user](https://support.zoom.us/hc/en-
        us/articles/201363173-Zoom-user-types-roles). * `1` - Basic. * `2` - Licensed. *
        `4` - Unassigned without Meetings Basic. * <del>`99` - None. You can only set
        this value if the user was created using the `ssoCreate` value for `action`
        parameter in... One of: [1, 2, 4, 99].
    use_pmi: Optional. Whether to use a [personal meeting ID
        (PMI)](https://developers.zoom.us/docs/api/rest/using-zoom-apis/#understanding-
        personal-meeting-id-pmi) for instant meetings.
    vanity_name: Optional. The user's personal meeting room name.
    display_name: Optional. The user's display name. This value cannot contain more than
        ten Chinese characters.
    zoom_one_type: Optional. The Zoom Workplace plan option. `0` - Turn off Zoom
        Workplace license. `16` - Zoom Workplace Business Plus with US/CA Unlimited.
        `32` - Zoom Workplace Business Plus with UK/IR Unlimited. `64` - Zoom Workplace
        Business Plus with AU/NZ Unlimited. `128` - Zoom Workplace Business Plus with
        Japan... One of: [0, 16, 32, 64, 128, 33554432, 134217728, 268435456, 536870912,
        1073741824, 4398046511104, 4294967296, 8589934592, 17179869184, 34359738368,
        68719476736, 137438953472, 274877906944, 549755813888, 1099511627776,
        2199023255552, 18014398509481984, 72057594037927940, 144115188075855870,
        576460752303423500].
    plan_united_type: Optional. The Zoom United type and license. * `1` - Zoom United
        Pro-United with US/CA Unlimited. * `2` - Zoom United Pro-United with UK/IR
        Unlimited. * `4` - Zoom United Pro-United with AU/NZ Unlimited. * `8` - Zoom
        United Pro-United with Global Select. * `16` - Zoom United Pro-United with Zoom
        Phone Pro. *... One of: ['1', '2', '4', '8', '16', '32', '64', '128', '256',
        '512', '1024', '2048', '4096', '8192', '16384', '32768', '65536', '131072',
        'none'].
    feature: Optional. The information about the user's features. If the value is set to
        false, will remove user from Zoom Phone. All numbers and phones assigned to the
        users will become unassigned.
    about_me: Optional. The user's self-introduction. Hyperlinks or HTML code not
        allowed in this field.
    linkedin_url: Optional. The user's LinkedIn link. The URL must contain
        `linkedin.com`.
    license_info_list: Optional. A list of license information used to specify the
        appropriate license type, license option, and license subscription reference ID.
        This list is only for accounts with multiple subscription plans enabled.
        """
        return await self._call("PATCH", f"/users/{user_id}", params=self._clean({"login_type": login_type, "remove_tsp_credentials": remove_tsp_credentials}), json_body=self._clean({"cms_user_id": cms_user_id, "company": company, "custom_attributes": custom_attributes, "dept": dept, "first_name": first_name, "group_id": group_id, "division_ids": division_ids, "host_key": host_key, "job_title": job_title, "cost_center": cost_center, "language": language, "last_name": last_name, "location": location, "manager": manager, "phone_country": phone_country, "phone_number": phone_number, "phone_numbers": phone_numbers, "pmi": pmi, "pronouns": pronouns, "pronouns_option": pronouns_option, "timezone": timezone, "type": type, "use_pmi": use_pmi, "vanity_name": vanity_name, "display_name": display_name, "zoom_one_type": zoom_one_type, "plan_united_type": plan_united_type, "feature": feature, "about_me": about_me, "linkedin_url": linkedin_url, "license_info_list": license_info_list}))

    async def list_user_assistants(self, user_id: str) -> object:
        """List user assistants

API: GET /users/{userId}/assistants

Args:
    user_id: Required. The user's user ID or email address. For user-level apps, pass
        the `me` value.
        """
        return await self._call("GET", f"/users/{user_id}/assistants", params=None, json_body=None)

    async def add_assistants(self, user_id: str, assistants: list[dict] | None = None) -> object:
        """Add assistants

API: POST /users/{userId}/assistants

Args:
    user_id: Required. The user's user ID or email address. For user-level apps, pass
        the `me` value.
    assistants: Optional. List of user's assistants.
        """
        return await self._call("POST", f"/users/{user_id}/assistants", params=None, json_body=self._clean({"assistants": assistants}))

    async def delete_user_assistants(self, user_id: str) -> object:
        """Delete user assistants

API: DELETE /users/{userId}/assistants

Args:
    user_id: Required. The user's user ID or email address. For user-level apps, pass
        the `me` value.
        """
        return await self._call("DELETE", f"/users/{user_id}/assistants", params=None, json_body=None)

    async def delete_a_user_assistant(self, user_id: str, assistant_id: str) -> object:
        """Delete a user assistant

API: DELETE /users/{userId}/assistants/{assistantId}

Args:
    user_id: Required. The user's user ID or email address. For user-level apps, pass
        the `me` value.
    assistant_id: Required. Assistant ID.
        """
        return await self._call("DELETE", f"/users/{user_id}/assistants/{assistant_id}", params=None, json_body=None)

    async def list_a_user_s_collaboration_devices(self, user_id: str) -> object:
        """List a user's collaboration devices

API: GET /users/{userId}/collaboration_devices

Args:
    user_id: Required. The user's user ID or email address. For user-level apps, pass
        the `me` value.
        """
        return await self._call("GET", f"/users/{user_id}/collaboration_devices", params=None, json_body=None)

    async def get_collaboration_device_detail(self, user_id: str, collaboration_device_id: str) -> object:
        """Get collaboration device detail

API: GET /users/{userId}/collaboration_devices/{collaborationDeviceId}

Args:
    user_id: Required. The user's user ID or email address. For user-level apps, pass
        the `me` value.
    collaboration_device_id: Required. The collaboration device ID.
        """
        return await self._call("GET", f"/users/{user_id}/collaboration_devices/{collaboration_device_id}", params=None, json_body=None)

    async def update_a_user_s_email(self, user_id: str, email: str) -> object:
        """Update a user's email

API: PUT /users/{userId}/email

Args:
    user_id: Required. The users's user ID or email address. For user-level apps, pass
        the `me` value.
    email: Required. User's email. The length should be less than 128 characters.
        """
        return await self._call("PUT", f"/users/{user_id}/email", params=None, json_body=self._clean({"email": email}))

    async def get_meeting_summary_templates(self, user_id: str) -> object:
        """Get meeting summary templates

API: GET /users/{userId}/meeting_summary_templates

Args:
    user_id: Required. current user's id
        """
        return await self._call("GET", f"/users/{user_id}/meeting_summary_templates", params=None, json_body=None)

    async def get_meeting_template_detail(self, user_id: str, meeting_template_id: str) -> object:
        """Get meeting template detail

API: GET /users/{userId}/meeting_templates/{meetingTemplateId}

Args:
    user_id: Required. The user's user ID or email address. For user-level apps, pass
        the `me` value.
    meeting_template_id: Required. The meeting template ID.
        """
        return await self._call("GET", f"/users/{user_id}/meeting_templates/{meeting_template_id}", params=None, json_body=None)

    async def update_a_user_s_password(self, user_id: str, password: str) -> object:
        """Update a user's password

API: PUT /users/{userId}/password

Args:
    user_id: Required. The user's user ID or email address. For user-level apps, pass
        the `me` value.
    password: Required. User password. Should be fewer than 32 characters. **Note** If
        the account owner or admin has enabled [enhanced password
        requirements](https://support.zoom.us/hc/en-us/articles/360034675592-Advanced-
        security-settings#h_fa9186e4-6818-4f7a-915c-2e25c19f0acd), the value provided in
        this field must...
        """
        return await self._call("PUT", f"/users/{user_id}/password", params=None, json_body=self._clean({"password": password}))

    async def get_user_permissions(self, user_id: str) -> object:
        """Get user permissions

API: GET /users/{userId}/permissions

Args:
    user_id: Required. The user's user ID or email address. For user-level apps, pass
        the `me` value.
        """
        return await self._call("GET", f"/users/{user_id}/permissions", params=None, json_body=None)

    async def upload_a_user_s_profile_picture(self, user_id: str, file_content_base64: str, filename: str) -> object:
        """Upload a user's profile picture

API: POST /users/{userId}/picture

Args:
    user_id: Required. The user's user ID or email address. For user-level apps, pass
        the `me` value.

file_content_base64: Required. The file's raw bytes, base64-encoded.
filename: Required. The file name to send with the upload.
        """
        return await self._call_multipart(
            "POST", f"/users/{user_id}/picture", field_name="pic_file",
            file_content_base64=file_content_base64, filename=filename,
        )

    async def delete_a_user_s_profile_picture(self, user_id: str) -> object:
        """Delete a user's profile picture

API: DELETE /users/{userId}/picture

Args:
    user_id: Required. The user's user ID or email address. For user-level apps, pass
        the `me` value.
        """
        return await self._call("DELETE", f"/users/{user_id}/picture", params=None, json_body=None)

    async def get_a_user_presence_status(self, user_id: str) -> object:
        """Get a user presence status

API: GET /users/{userId}/presence_status

Args:
    user_id: Required. The user ID, email address, or member ID. The user can be either
        a company user or an external user.
        """
        return await self._call("GET", f"/users/{user_id}/presence_status", params=None, json_body=None)

    async def update_a_user_s_presence_status(self, user_id: str) -> object:
        """Update a user's presence status

API: PUT /users/{userId}/presence_status

Args:
    user_id: Required. The user ID or email address. For user-level apps, pass the `me`
        value.
        """
        return await self._call("PUT", f"/users/{user_id}/presence_status", params=None, json_body={})

    async def list_user_schedulers(self, user_id: str) -> object:
        """List user schedulers

API: GET /users/{userId}/schedulers

Args:
    user_id: Required. The user's user ID or email address. For user-level apps, pass
        the `me` value.
        """
        return await self._call("GET", f"/users/{user_id}/schedulers", params=None, json_body=None)

    async def delete_user_schedulers(self, user_id: str) -> object:
        """Delete user schedulers

API: DELETE /users/{userId}/schedulers

Args:
    user_id: Required. The user's user ID or email address. For user-level apps, pass
        the `me` value.
        """
        return await self._call("DELETE", f"/users/{user_id}/schedulers", params=None, json_body=None)

    async def delete_a_scheduler(self, user_id: str, scheduler_id: str) -> object:
        """Delete a scheduler

API: DELETE /users/{userId}/schedulers/{schedulerId}

Args:
    user_id: Required. The user's user ID or email address. For user-level apps, pass
        the `me` value.
    scheduler_id: Required. Scheduler's ID.
        """
        return await self._call("DELETE", f"/users/{user_id}/schedulers/{scheduler_id}", params=None, json_body=None)

    async def get_user_settings(self, user_id: str, login_type: int | None = None, option: str | None = None, custom_query_fields: str | None = None) -> object:
        """Get user settings

API: GET /users/{userId}/settings

Args:
    user_id: Required. The user ID or email address of the user. For user-level apps,
        pass the `me` value.
    login_type: Optional. The user's login method. * `0` - Facebook OAuth * `1` - Google
        OAuth * `24` - Apple OAuth * `27` - Microsoft OAuth * `97` - Mobile device *
        `98` - RingCentral OAuth * `99` - API user * `100` - Zoom Work email * `101` -
        Single Sign-On (SSO) These login methods are only available in China: * `11`
        -... One of: [0, 1, 11, 21, 23, 24, 27, 97, 98, 99, 100, 101].
    option: Optional. Optional query parameters. * `meeting_authentication` - Use this
        query parameter to view the [meeting authentication
        settings](https://support.zoom.us/hc/en-us/articles/360037117472-Authentication-
        Profiles-for-Meetings-and-Webinars) applied to the user's account. *
        `recording_authentication` - Use... One of: ['meeting_authentication',
        'recording_authentication', 'meeting_security'].
    custom_query_fields: Optional. Provide the name of the field to filter the response.
        For example, if you provide `host_video` as the value of this field, you'll get
        a response similar to this. { schedule_meeting: { host_video: false } } To
        provide multiple values, separate them with commas, like
        `host_video,participant_video`.
        """
        return await self._call("GET", f"/users/{user_id}/settings", params=self._clean({"login_type": login_type, "option": option, "custom_query_fields": custom_query_fields}), json_body=None)

    async def update_user_settings(self, user_id: str, option: str | None = None) -> object:
        """Update user settings

API: PATCH /users/{userId}/settings

Args:
    user_id: Required. The user's user ID or email address. For user-level apps, pass
        the `me` value.
    option: Optional. The optional query parameters: * `meeting_authentication` &mdash;
        Use this query parameter to view the [meeting authentication
        settings](https://support.zoom.us/hc/en-us/articles/360037117472-Authentication-
        Profiles-for-Meetings-and-Webinars) applied to the user's account. *... One of:
        ['meeting_authentication', 'recording_authentication', 'meeting_security'].
        """
        return await self._call("PATCH", f"/users/{user_id}/settings", params=self._clean({"option": option}), json_body={})

    async def user_upload_virtual_background_files(self, user_id: str, file_content_base64: str, filename: str) -> object:
        """Upload Virtual Background files

API: POST /users/{userId}/settings/virtual_backgrounds

Args:
    user_id: Required. The user's ID. To get a user's ID, use the [**List users**](/api-
        reference/zoom-api/ma#operation/users) API. For user-level apps, pass the `me`
        value instead of the user ID value.

file_content_base64: Required. The file's raw bytes, base64-encoded.
filename: Required. The file name to send with the upload.
        """
        return await self._call_multipart(
            "POST", f"/users/{user_id}/settings/virtual_backgrounds", field_name="file",
            file_content_base64=file_content_base64, filename=filename,
        )

    async def user_delete_virtual_background_files(self, user_id: str, file_ids: str | None = None) -> object:
        """Delete Virtual Background files

API: DELETE /users/{userId}/settings/virtual_backgrounds

Args:
    user_id: Required. The user's ID. To get a user's ID, use the [**List
        users**](/docs/api-reference/zoom-api/ma#operation/users) API. For user-level
        apps, pass the `me` value instead of the user ID value.
    file_ids: Optional. A comma-separated list of the Virtual Background file IDs to
        delete.
        """
        return await self._call("DELETE", f"/users/{user_id}/settings/virtual_backgrounds", params=self._clean({"file_ids": file_ids}), json_body=None)

    async def update_user_status(self, user_id: str, action: str, transfer_events: bool | None = None, transfer_email: str | None = None) -> object:
        """Update user status

API: PUT /users/{userId}/status

Args:
    user_id: Required. The user's user ID or email address. For user-level apps, pass
        the `me` value.
    action: Required. The action types. `activate` - Activate a deactivated user.
        `deactivate` - Deactivate a user. `clock_in` - Clock in a user. `clock_out` -
        Clock out a user. One of: ['activate', 'deactivate', 'clock_in', 'clock_out'].
    transfer_events: Optional. Indicates whether to transfer Zoom Events hub assets.
        This option is supported only for user deactivation operations. When
        `transfer_events` is set to `true`, the `transfer_email` field is required. Upon
        user deactivation, the user’s Zoom Events hub assets will be transferred to the
        specified...
    transfer_email: Optional. Transfer email. The email address of the target user who
        will receive the Zoom Events hub assets transferred from the deactivated user.
        This field is **required** when `transfer_events` is set to `true`.
        """
        return await self._call("PUT", f"/users/{user_id}/status", params=None, json_body=self._clean({"action": action, "transfer_events": transfer_events, "transfer_email": transfer_email}))

    async def get_a_user_s_token(self, user_id: str, type: str = "token", ttl: int = 7200, meeting_id: str | None = None) -> object:
        """Get a user's token

API: GET /users/{userId}/token

Args:
    user_id: Required. The user's user ID or email address. For user-level apps, pass
        the `me` value.
    type: Optional. The user token type. * `zak` - A Zoom Access Key (ZAK) is used to
        generate a URL to start meetings. See [Getting a Zoom Access Key
        (ZAK)](https://developers.zoom.us/docs/meeting-sdk/auth/#start-meetings-and-
        webinars-with-a-zoom-users-zak-token) for details. The ZAK's expiration time is
        two hours.... One of: ['token', 'zak', 'onbehalf'].
    ttl: Optional. The ZAK/onbehalf expiration time to live (TTL), in seconds. To update
        the user's ZAK/onbehalf TTL, use this field with the `zak` or `onbehalf` value
        for the `type` query parameter. Defaults to `7200` or `7776000` (90 days) for
        API users. The maximum value is one year.
    meeting_id: Optional. The meeting's ID, use this field with the `onbehalf` value for
        the `type` query parameter.
        """
        return await self._call("GET", f"/users/{user_id}/token", params=self._clean({"type": type, "ttl": ttl, "meeting_id": meeting_id}), json_body=None)

    async def revoke_a_user_s_sso_token(self, user_id: str) -> object:
        """Revoke a user's SSO token

API: DELETE /users/{userId}/token

Args:
    user_id: Required. The user's user ID or email address. For user-level apps, pass
        the `me` value.
        """
        return await self._call("DELETE", f"/users/{user_id}/token", params=None, json_body=None)
