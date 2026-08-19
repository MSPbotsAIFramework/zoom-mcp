from collections.abc import Callable
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .._json import dump_json_capped
from ..api_client import ZoomClient, ZoomError
from ._common import NO_TOKEN

# Zoom's own OpenAPI spec (developers.zoom.us/api-hub/users/methods/endpoints.json)
# documents the "List users" page_size ceiling as 2000.
_USERS_MAX_PAGE_SIZE = 2000


def register(mcp: FastMCP, client_factory: Callable[[], ZoomClient | None]) -> None:

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def zoom_list_users(
        status: Annotated[
            str,
            Field(description="Account status filter. One of: active, inactive, pending."),
        ] = "active",
        page_size: Annotated[
            int | None, Field(description="Records per page (max 2000, default 30).")
        ] = 30,
        role_id: Annotated[
            str | None, Field(description="Filter to users with this role ID.")
        ] = None,
        page_number: Annotated[
            str | None,
            Field(description="Deprecated by Zoom; prefer next_page_token instead."),
        ] = None,
        include_fields: Annotated[
            str | None,
            Field(description="Extra attribute to include. One of: custom_attributes, host_key."),
        ] = None,
        next_page_token: Annotated[
            str | None,
            Field(description="Token from a previous response to fetch the next page."),
        ] = None,
        license: Annotated[
            str | None, Field(description="Filter to users holding this license type.")
        ] = None,
    ) -> str:
        """List users on the account, optionally filtered by status, role, or license."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        if page_size is not None:
            page_size = min(page_size, _USERS_MAX_PAGE_SIZE)
        try:
            result = await client.list_users(
                status=status,
                page_size=page_size,
                role_id=role_id,
                page_number=page_number,
                include_fields=include_fields,
                next_page_token=next_page_token,
                license=license,
            )
            return dump_json_capped(result)
        except ZoomError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
    async def zoom_create_users(
        action: Annotated[
            str,
            Field(
                description=(
                    "How to create the user. One of: create (emails a confirmation "
                    "link), autoCreate, custCreate, ssoCreate."
                )
            ),
        ],
        user_info: Annotated[
            dict | None,
            Field(description="User fields, e.g. {'email': ..., 'type': ..., 'first_name': ...}."),
        ] = None,
    ) -> str:
        """Create a new user account on the account."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.create_users(action=action, user_info=user_info)
            return dump_json_capped(result)
        except ZoomError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def zoom_check_a_user_email(
        email: Annotated[str, Field(description="The email address to check.")],
    ) -> str:
        """Check whether an email address is already registered as a user on the account."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.check_a_user_email(email=email)
            return dump_json_capped(result)
        except ZoomError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def zoom_get_a_user(
        user_id: Annotated[
            str, Field(description="User ID or email address. Use 'me' for the calling user.")
        ],
        login_type: Annotated[
            int | None,
            Field(description="Login method to disambiguate duplicate emails, per Zoom's login-type codes."),
        ] = None,
        encrypted_email: Annotated[
            bool | None, Field(description="Whether user_id is an encrypted email address.")
        ] = False,
        search_by_unique_id: Annotated[
            bool | None, Field(description="Whether user_id is an employee unique ID.")
        ] = None,
    ) -> str:
        """Get a single user's profile by ID or email."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get_a_user(
                user_id=user_id,
                login_type=login_type,
                encrypted_email=encrypted_email,
                search_by_unique_id=search_by_unique_id,
            )
            return dump_json_capped(result)
        except ZoomError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=True))
    async def zoom_delete_a_user(
        user_id: Annotated[
            str, Field(description="User ID or email address. Use 'me' for the calling user.")
        ],
        encrypted_email: Annotated[
            bool | None, Field(description="Whether user_id is an encrypted email address.")
        ] = False,
        action: Annotated[
            str,
            Field(
                description=(
                    "disassociate (remove from account, recoverable) or delete "
                    "(permanent removal)."
                )
            ),
        ] = "disassociate",
        transfer_email: Annotated[
            str | None,
            Field(description="Target user's email to receive transferred assets; required with several transfer_* flags."),
        ] = None,
        transfer_meeting: Annotated[bool | None, Field(description="Transfer the user's meetings.")] = None,
        transfer_webinar: Annotated[bool | None, Field(description="Transfer the user's webinars.")] = None,
        transfer_recording: Annotated[bool | None, Field(description="Transfer the user's recordings.")] = None,
        transfer_whiteboard: Annotated[bool | None, Field(description="Transfer the user's whiteboards.")] = None,
        transfer_clipfiles: Annotated[bool | None, Field(description="Transfer the user's clip files.")] = None,
        transfer_notes: Annotated[bool | None, Field(description="Transfer the user's notes.")] = None,
        transfer_visitors: Annotated[bool | None, Field(description="Transfer the user's visitor data.")] = None,
        transfer_docs: Annotated[bool | None, Field(description="Transfer the user's docs.")] = None,
        transfer_events: Annotated[
            bool | None,
            Field(description="Transfer the user's Zoom Events hub assets to transfer_email."),
        ] = True,
    ) -> str:
        """Remove a user from the account (disassociate) or permanently delete them."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.delete_a_user(
                user_id=user_id,
                encrypted_email=encrypted_email,
                action=action,
                transfer_email=transfer_email,
                transfer_meeting=transfer_meeting,
                transfer_webinar=transfer_webinar,
                transfer_recording=transfer_recording,
                transfer_whiteboard=transfer_whiteboard,
                transfer_clipfiles=transfer_clipfiles,
                transfer_notes=transfer_notes,
                transfer_visitors=transfer_visitors,
                transfer_docs=transfer_docs,
                transfer_events=transfer_events,
            )
            return dump_json_capped(result)
        except ZoomError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=True))
    async def zoom_update_a_user(
        user_id: Annotated[
            str, Field(description="User ID or email address. Use 'me' for the calling user.")
        ],
        login_type: Annotated[int | None, Field(description="The user's login method code.")] = None,
        remove_tsp_credentials: Annotated[
            bool | None, Field(description="Remove the user's TSP (telephony) credentials.")
        ] = None,
        cms_user_id: Annotated[str | None, Field(description="The user's Kaltura user ID.")] = None,
        company: Annotated[str | None, Field(description="The user's company name.")] = None,
        custom_attributes: Annotated[
            list[dict] | None, Field(description="Custom attribute objects to assign to the user.")
        ] = None,
        dept: Annotated[str | None, Field(description="The user's department.")] = None,
        first_name: Annotated[str | None, Field(description="The user's first name.")] = None,
        group_id: Annotated[
            str | None, Field(description="Group ID to add a pending user to, from zoom_list_groups.")
        ] = None,
        division_ids: Annotated[
            list[str] | None, Field(description="Division IDs to assign (currently one supported).")
        ] = None,
        host_key: Annotated[str | None, Field(description="The user's host key.")] = None,
        job_title: Annotated[str | None, Field(description="The user's job title.")] = None,
        cost_center: Annotated[str | None, Field(description="The user's cost center.")] = None,
        language: Annotated[str | None, Field(description="The user's display language.")] = None,
        last_name: Annotated[str | None, Field(description="The user's last name.")] = None,
        location: Annotated[str | None, Field(description="The user's location.")] = None,
        manager: Annotated[
            str | None, Field(description="Manager's email or display name within the same account.")
        ] = None,
        phone_country: Annotated[
            str | None, Field(description="Deprecated by Zoom; use phone_numbers instead.")
        ] = None,
        phone_number: Annotated[
            str | None, Field(description="Deprecated by Zoom; use phone_numbers instead.")
        ] = None,
        phone_numbers: Annotated[
            list[dict] | None, Field(description="Phone number objects to assign to the user.")
        ] = None,
        pmi: Annotated[int | None, Field(description="The user's personal meeting ID.")] = None,
        pronouns: Annotated[str | None, Field(description="The user's pronouns.")] = None,
        pronouns_option: Annotated[
            int | None,
            Field(description="Pronoun display setting: 1 ask each time, 2 always show, 3 never show."),
        ] = None,
        timezone: Annotated[str | None, Field(description="The user's timezone identifier.")] = None,
        type: Annotated[
            int | None,
            Field(description="Zoom user type: 1 Basic, 2 Licensed, 4 Unassigned without Meetings Basic."),
        ] = None,
        use_pmi: Annotated[
            bool | None, Field(description="Use the personal meeting ID for instant meetings.")
        ] = False,
        vanity_name: Annotated[str | None, Field(description="The user's personal meeting room name.")] = None,
        display_name: Annotated[str | None, Field(description="The user's display name.")] = None,
        zoom_one_type: Annotated[
            int | None, Field(description="Zoom Workplace plan option code.")
        ] = None,
        plan_united_type: Annotated[
            str | None, Field(description="Zoom United plan/license type code.")
        ] = None,
        feature: Annotated[
            dict | None, Field(description="Feature flags object, e.g. to remove Zoom Phone access.")
        ] = None,
        about_me: Annotated[str | None, Field(description="The user's self-introduction text.")] = None,
        linkedin_url: Annotated[
            str | None, Field(description="The user's LinkedIn profile URL (must contain linkedin.com).")
        ] = None,
        license_info_list: Annotated[
            list[dict] | None,
            Field(description="License objects for accounts with multiple subscription plans."),
        ] = None,
    ) -> str:
        """Update a user's profile fields, licensing, or feature settings."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.update_a_user(
                user_id=user_id,
                login_type=login_type,
                remove_tsp_credentials=remove_tsp_credentials,
                cms_user_id=cms_user_id,
                company=company,
                custom_attributes=custom_attributes,
                dept=dept,
                first_name=first_name,
                group_id=group_id,
                division_ids=division_ids,
                host_key=host_key,
                job_title=job_title,
                cost_center=cost_center,
                language=language,
                last_name=last_name,
                location=location,
                manager=manager,
                phone_country=phone_country,
                phone_number=phone_number,
                phone_numbers=phone_numbers,
                pmi=pmi,
                pronouns=pronouns,
                pronouns_option=pronouns_option,
                timezone=timezone,
                type=type,
                use_pmi=use_pmi,
                vanity_name=vanity_name,
                display_name=display_name,
                zoom_one_type=zoom_one_type,
                plan_united_type=plan_united_type,
                feature=feature,
                about_me=about_me,
                linkedin_url=linkedin_url,
                license_info_list=license_info_list,
            )
            return dump_json_capped(result)
        except ZoomError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def zoom_get_user_permissions(
        user_id: Annotated[
            str, Field(description="User ID or email address. Use 'me' for the calling user.")
        ],
    ) -> str:
        """Get the operations a user is permitted to perform."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get_user_permissions(user_id=user_id)
            return dump_json_capped(result)
        except ZoomError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=True))
    async def zoom_update_user_status(
        user_id: Annotated[
            str, Field(description="User ID or email address. Use 'me' for the calling user.")
        ],
        action: Annotated[
            str,
            Field(description="One of: activate, deactivate, clock_in, clock_out."),
        ],
        transfer_events: Annotated[
            bool | None,
            Field(description="On deactivation, transfer Zoom Events hub assets to transfer_email."),
        ] = None,
        transfer_email: Annotated[
            str | None,
            Field(description="Target user's email for transferred assets; required if transfer_events is true."),
        ] = None,
    ) -> str:
        """Activate, deactivate, or clock a user in/out."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.update_user_status(
                user_id=user_id,
                action=action,
                transfer_events=transfer_events,
                transfer_email=transfer_email,
            )
            return dump_json_capped(result)
        except ZoomError as e:
            return e.to_envelope()
