import json
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..api_client import ZoomClient, ZoomError
from ._common import NO_TOKEN


def register(mcp: FastMCP, client_factory: Callable[[], ZoomClient | None]) -> None:

    @mcp.tool()
    async def zoom_list_users(status: str = "active", page_size: int = 30, role_id: str | None = None, page_number: str | None = None, include_fields: str | None = None, next_page_token: str | None = None, license: str | None = None) -> str:
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
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.list_users(status=status, page_size=page_size, role_id=role_id, page_number=page_number, include_fields=include_fields, next_page_token=next_page_token, license=license)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_create_users(action: str, user_info: dict | None = None) -> str:
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
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.create_users(action=action, user_info=user_info)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_check_a_user_email(email: str) -> str:
        """Check a user email

API: GET /users/email

Args:
    email: Required. The email address to be verified.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.check_a_user_email(email=email)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_bulk_update_features_for_users(feature_type: str, feature_value: str, users: list[dict], subscription_id: str | None = None, license_info_list: list[dict] | None = None) -> str:
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
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.bulk_update_features_for_users(feature_type=feature_type, feature_value=feature_value, users=users, subscription_id=subscription_id, license_info_list=license_info_list)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_get_the_user_s_zak() -> str:
        """Get the user's ZAK

API: GET /users/me/zak

        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get_the_user_s_zak()
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_get_user_summary() -> str:
        """Get user summary

API: GET /users/summary

        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get_user_summary()
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_check_a_user_s_pm_room(vanity_name: str) -> str:
        """Check a user's PM room

API: GET /users/vanity_name

Args:
    vanity_name: Required. Personal meeting room name.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.check_a_user_s_pm_room(vanity_name=vanity_name)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_get_a_user(user_id: str, login_type: int | None = None, encrypted_email: bool = False, search_by_unique_id: bool | None = None) -> str:
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
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get_a_user(user_id=user_id, login_type=login_type, encrypted_email=encrypted_email, search_by_unique_id=search_by_unique_id)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_delete_a_user(user_id: str, encrypted_email: bool = False, action: str = "disassociate", transfer_email: str | None = None, transfer_meeting: bool | None = None, transfer_webinar: bool | None = None, transfer_recording: bool | None = None, transfer_whiteboard: bool | None = None, transfer_clipfiles: bool | None = None, transfer_notes: bool | None = None, transfer_visitors: bool | None = None, transfer_docs: bool | None = None, transfer_events: bool = True) -> str:
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
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.delete_a_user(user_id=user_id, encrypted_email=encrypted_email, action=action, transfer_email=transfer_email, transfer_meeting=transfer_meeting, transfer_webinar=transfer_webinar, transfer_recording=transfer_recording, transfer_whiteboard=transfer_whiteboard, transfer_clipfiles=transfer_clipfiles, transfer_notes=transfer_notes, transfer_visitors=transfer_visitors, transfer_docs=transfer_docs, transfer_events=transfer_events)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_update_a_user(user_id: str, login_type: int | None = None, remove_tsp_credentials: bool | None = None, cms_user_id: str | None = None, company: str | None = None, custom_attributes: list[dict] | None = None, dept: str | None = None, first_name: str | None = None, group_id: str | None = None, division_ids: list[str] | None = None, host_key: str | None = None, job_title: str | None = None, cost_center: str | None = None, language: str | None = None, last_name: str | None = None, location: str | None = None, manager: str | None = None, phone_country: str | None = None, phone_number: str | None = None, phone_numbers: list[dict] | None = None, pmi: int | None = None, pronouns: str | None = None, pronouns_option: int | None = None, timezone: str | None = None, type: int | None = None, use_pmi: bool = False, vanity_name: str | None = None, display_name: str | None = None, zoom_one_type: int | None = None, plan_united_type: str | None = None, feature: dict | None = None, about_me: str | None = None, linkedin_url: str | None = None, license_info_list: list[dict] | None = None) -> str:
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
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.update_a_user(user_id=user_id, login_type=login_type, remove_tsp_credentials=remove_tsp_credentials, cms_user_id=cms_user_id, company=company, custom_attributes=custom_attributes, dept=dept, first_name=first_name, group_id=group_id, division_ids=division_ids, host_key=host_key, job_title=job_title, cost_center=cost_center, language=language, last_name=last_name, location=location, manager=manager, phone_country=phone_country, phone_number=phone_number, phone_numbers=phone_numbers, pmi=pmi, pronouns=pronouns, pronouns_option=pronouns_option, timezone=timezone, type=type, use_pmi=use_pmi, vanity_name=vanity_name, display_name=display_name, zoom_one_type=zoom_one_type, plan_united_type=plan_united_type, feature=feature, about_me=about_me, linkedin_url=linkedin_url, license_info_list=license_info_list)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_list_user_assistants(user_id: str) -> str:
        """List user assistants

API: GET /users/{userId}/assistants

Args:
    user_id: Required. The user's user ID or email address. For user-level apps, pass
        the `me` value.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.list_user_assistants(user_id=user_id)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_add_assistants(user_id: str, assistants: list[dict] | None = None) -> str:
        """Add assistants

API: POST /users/{userId}/assistants

Args:
    user_id: Required. The user's user ID or email address. For user-level apps, pass
        the `me` value.
    assistants: Optional. List of user's assistants.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.add_assistants(user_id=user_id, assistants=assistants)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_delete_user_assistants(user_id: str) -> str:
        """Delete user assistants

API: DELETE /users/{userId}/assistants

Args:
    user_id: Required. The user's user ID or email address. For user-level apps, pass
        the `me` value.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.delete_user_assistants(user_id=user_id)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_delete_a_user_assistant(user_id: str, assistant_id: str) -> str:
        """Delete a user assistant

API: DELETE /users/{userId}/assistants/{assistantId}

Args:
    user_id: Required. The user's user ID or email address. For user-level apps, pass
        the `me` value.
    assistant_id: Required. Assistant ID.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.delete_a_user_assistant(user_id=user_id, assistant_id=assistant_id)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_list_a_user_s_collaboration_devices(user_id: str) -> str:
        """List a user's collaboration devices

API: GET /users/{userId}/collaboration_devices

Args:
    user_id: Required. The user's user ID or email address. For user-level apps, pass
        the `me` value.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.list_a_user_s_collaboration_devices(user_id=user_id)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_get_collaboration_device_detail(user_id: str, collaboration_device_id: str) -> str:
        """Get collaboration device detail

API: GET /users/{userId}/collaboration_devices/{collaborationDeviceId}

Args:
    user_id: Required. The user's user ID or email address. For user-level apps, pass
        the `me` value.
    collaboration_device_id: Required. The collaboration device ID.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get_collaboration_device_detail(user_id=user_id, collaboration_device_id=collaboration_device_id)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_update_a_user_s_email(user_id: str, email: str) -> str:
        """Update a user's email

API: PUT /users/{userId}/email

Args:
    user_id: Required. The users's user ID or email address. For user-level apps, pass
        the `me` value.
    email: Required. User's email. The length should be less than 128 characters.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.update_a_user_s_email(user_id=user_id, email=email)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_get_meeting_summary_templates(user_id: str) -> str:
        """Get meeting summary templates

API: GET /users/{userId}/meeting_summary_templates

Args:
    user_id: Required. current user's id
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get_meeting_summary_templates(user_id=user_id)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_get_meeting_template_detail(user_id: str, meeting_template_id: str) -> str:
        """Get meeting template detail

API: GET /users/{userId}/meeting_templates/{meetingTemplateId}

Args:
    user_id: Required. The user's user ID or email address. For user-level apps, pass
        the `me` value.
    meeting_template_id: Required. The meeting template ID.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get_meeting_template_detail(user_id=user_id, meeting_template_id=meeting_template_id)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_update_a_user_s_password(user_id: str, password: str) -> str:
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
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.update_a_user_s_password(user_id=user_id, password=password)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_get_user_permissions(user_id: str) -> str:
        """Get user permissions

API: GET /users/{userId}/permissions

Args:
    user_id: Required. The user's user ID or email address. For user-level apps, pass
        the `me` value.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get_user_permissions(user_id=user_id)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_upload_a_user_s_profile_picture(user_id: str, file_content_base64: str, filename: str) -> str:
        """Upload a user's profile picture

API: POST /users/{userId}/picture

Args:
    user_id: Required. The user's user ID or email address. For user-level apps, pass
        the `me` value.

file_content_base64: Required. The file's raw bytes, base64-encoded.
filename: Required. The file name to send with the upload.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.upload_a_user_s_profile_picture(user_id=user_id, file_content_base64=file_content_base64, filename=filename)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_delete_a_user_s_profile_picture(user_id: str) -> str:
        """Delete a user's profile picture

API: DELETE /users/{userId}/picture

Args:
    user_id: Required. The user's user ID or email address. For user-level apps, pass
        the `me` value.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.delete_a_user_s_profile_picture(user_id=user_id)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_get_a_user_presence_status(user_id: str) -> str:
        """Get a user presence status

API: GET /users/{userId}/presence_status

Args:
    user_id: Required. The user ID, email address, or member ID. The user can be either
        a company user or an external user.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get_a_user_presence_status(user_id=user_id)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_update_a_user_s_presence_status(user_id: str) -> str:
        """Update a user's presence status

API: PUT /users/{userId}/presence_status

Args:
    user_id: Required. The user ID or email address. For user-level apps, pass the `me`
        value.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.update_a_user_s_presence_status(user_id=user_id)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_list_user_schedulers(user_id: str) -> str:
        """List user schedulers

API: GET /users/{userId}/schedulers

Args:
    user_id: Required. The user's user ID or email address. For user-level apps, pass
        the `me` value.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.list_user_schedulers(user_id=user_id)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_delete_user_schedulers(user_id: str) -> str:
        """Delete user schedulers

API: DELETE /users/{userId}/schedulers

Args:
    user_id: Required. The user's user ID or email address. For user-level apps, pass
        the `me` value.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.delete_user_schedulers(user_id=user_id)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_delete_a_scheduler(user_id: str, scheduler_id: str) -> str:
        """Delete a scheduler

API: DELETE /users/{userId}/schedulers/{schedulerId}

Args:
    user_id: Required. The user's user ID or email address. For user-level apps, pass
        the `me` value.
    scheduler_id: Required. Scheduler's ID.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.delete_a_scheduler(user_id=user_id, scheduler_id=scheduler_id)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_get_user_settings(user_id: str, login_type: int | None = None, option: str | None = None, custom_query_fields: str | None = None) -> str:
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
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get_user_settings(user_id=user_id, login_type=login_type, option=option, custom_query_fields=custom_query_fields)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_update_user_settings(user_id: str, option: str | None = None) -> str:
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
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.update_user_settings(user_id=user_id, option=option)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_user_upload_virtual_background_files(user_id: str, file_content_base64: str, filename: str) -> str:
        """Upload Virtual Background files

API: POST /users/{userId}/settings/virtual_backgrounds

Args:
    user_id: Required. The user's ID. To get a user's ID, use the [**List users**](/api-
        reference/zoom-api/ma#operation/users) API. For user-level apps, pass the `me`
        value instead of the user ID value.

file_content_base64: Required. The file's raw bytes, base64-encoded.
filename: Required. The file name to send with the upload.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.user_upload_virtual_background_files(user_id=user_id, file_content_base64=file_content_base64, filename=filename)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_user_delete_virtual_background_files(user_id: str, file_ids: str | None = None) -> str:
        """Delete Virtual Background files

API: DELETE /users/{userId}/settings/virtual_backgrounds

Args:
    user_id: Required. The user's ID. To get a user's ID, use the [**List
        users**](/docs/api-reference/zoom-api/ma#operation/users) API. For user-level
        apps, pass the `me` value instead of the user ID value.
    file_ids: Optional. A comma-separated list of the Virtual Background file IDs to
        delete.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.user_delete_virtual_background_files(user_id=user_id, file_ids=file_ids)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_update_user_status(user_id: str, action: str, transfer_events: bool | None = None, transfer_email: str | None = None) -> str:
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
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.update_user_status(user_id=user_id, action=action, transfer_events=transfer_events, transfer_email=transfer_email)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_get_a_user_s_token(user_id: str, type: str = "token", ttl: int = 7200, meeting_id: str | None = None) -> str:
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
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get_a_user_s_token(user_id=user_id, type=type, ttl=ttl, meeting_id=meeting_id)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def zoom_revoke_a_user_s_sso_token(user_id: str) -> str:
        """Revoke a user's SSO token

API: DELETE /users/{userId}/token

Args:
    user_id: Required. The user's user ID or email address. For user-level apps, pass
        the `me` value.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.revoke_a_user_s_sso_token(user_id=user_id)
            return json.dumps(result, indent=2)
        except ZoomError as e:
            return f"Error: {e}"
