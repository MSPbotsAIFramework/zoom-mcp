import asyncio
import base64
from typing import Any

import httpx

from ._json import error_envelope

_TIMEOUT = httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0)
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}
_MAX_RETRIES = 3
_MAX_BACKOFF_SECONDS = 20.0

# One shared connection pool for the process lifetime. No credentials are
# ever stored on it — account/client credentials are passed per-request via
# ZoomClient instances built from the request-scoped contextvar (see
# server.py's credential isolation, which is what actually keeps tenants
# apart), so sharing this pool across tenants/requests is safe.
_http_client: httpx.AsyncClient | None = None


def _get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True)
    return _http_client


# status_code -> (error code, retryable). status_code 0 means a network/
# connection-level failure (no response at all).
_STATUS_TO_CODE: dict[int, tuple[str, bool]] = {
    0: ("upstream_error", True),
    400: ("invalid_argument", False),
    401: ("unauthorized", False),
    403: ("unauthorized", False),
    404: ("not_found", False),
    422: ("invalid_argument", False),
    429: ("rate_limited", True),
}


def _classify(status_code: int) -> tuple[str, bool]:
    if status_code in _STATUS_TO_CODE:
        return _STATUS_TO_CODE[status_code]
    if status_code >= 500:
        return "upstream_error", True
    return "invalid_argument", False


class ZoomError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"Zoom API error {status_code}: {message}")

    def to_envelope(self) -> str:
        code, retryable = _classify(self.status_code)
        return error_envelope(code, self.message, retryable)


class ZoomClient:
    """Async httpx client wrapping a subset of Zoom's Users Admin API
    (Users and Groups endpoints from https://developers.zoom.us/docs/api/users/).

    Auth is Server-to-Server OAuth (the "account_credentials" grant --
    Zoom's two-legged OAuth for backend automation, no user redirect):

      POST https://zoom.us/oauth/token
        ?grant_type=account_credentials&account_id=...
        Authorization: Basic base64(client_id:client_secret)
      -> {"access_token": "...", "expires_in": 3599, ...}

    The access token is valid for only 1 hour and there is no refresh
    token, so this client re-authenticates fresh on every single call
    rather than caching it across MCP requests, to stay fully stateless.
    Reuses the module-level connection pool (see _get_http_client) for
    both the token exchange and the API call, rather than opening a new
    connection per request.
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

    def _clean(self, params: dict | None) -> dict:
        if not params:
            return {}
        return {k: v for k, v in params.items() if v is not None}

    async def _login(self) -> str:
        client = _get_http_client()
        basic = base64.b64encode(f"{self._client_id}:{self._client_secret}".encode()).decode()
        resp = await self._send(
            client,
            "POST",
            self._oauth_url,
            headers={"Authorization": f"Basic {basic}"},
            params={"grant_type": "account_credentials", "account_id": self._account_id},
        )
        body = self._parse_body(resp)
        access_token = body.get("access_token") if isinstance(body, dict) else None
        if not access_token:
            raise ZoomError(resp.status_code or 502, "OAuth login did not return an access_token")
        return access_token

    async def _send(self, client: httpx.AsyncClient, method: str, url: str, **kwargs: Any) -> httpx.Response:
        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                resp = await client.request(method, url, **kwargs)
            except httpx.RequestError as e:
                last_exc = e
                if attempt < _MAX_RETRIES:
                    await asyncio.sleep(min(2**attempt, _MAX_BACKOFF_SECONDS))
                    continue
                raise ZoomError(0, f"{e or type(e).__name__} (url={url})") from e

            if resp.status_code in _RETRYABLE_STATUS and attempt < _MAX_RETRIES:
                await asyncio.sleep(self._retry_delay(resp, attempt))
                continue

            if resp.status_code >= 400:
                self._raise_for_status(resp)
            return resp

        # Unreachable in practice (loop always returns or raises above), but
        # keeps type checkers happy and guards against future edits.
        if last_exc:
            raise ZoomError(0, f"{last_exc}") from last_exc
        raise ZoomError(0, "request failed with no response")

    def _retry_delay(self, resp: httpx.Response, attempt: int) -> float:
        retry_after = resp.headers.get("Retry-After")
        if retry_after:
            try:
                return min(float(retry_after), _MAX_BACKOFF_SECONDS)
            except ValueError:
                pass
        return min(2**attempt, _MAX_BACKOFF_SECONDS)

    def _parse_body(self, resp: httpx.Response) -> Any:
        if not resp.content:
            return {}
        try:
            return resp.json()
        except ValueError:
            return {"raw_response": resp.text}

    def _raise_for_status(self, resp: httpx.Response) -> None:
        try:
            detail = resp.json()
            if isinstance(detail, dict):
                msg = detail.get("message") or detail.get("reason") or detail.get("error") or str(detail)
            else:
                msg = str(detail)
        except ValueError:
            msg = resp.text
        raise ZoomError(resp.status_code, msg)

    async def _call(
        self, method: str, path: str, params: dict | None = None, json_body: Any = None
    ) -> Any:
        client = _get_http_client()
        token = await self._login()
        headers = {"Authorization": f"Bearer {token}"}
        resp = await self._send(
            client,
            method,
            f"{self._api_base_url}{path}",
            headers=headers,
            params=self._clean(params),
            json=json_body,
        )
        return self._parse_body(resp)

    # ---- Groups ----

    async def list_groups(
        self, page_size: int | None = None, next_page_token: str | None = None
    ) -> Any:
        return await self._call(
            "GET", "/groups", params={"page_size": page_size, "next_page_token": next_page_token}
        )

    async def create_a_group(self, name: str | None = None) -> Any:
        return await self._call("POST", "/groups", json_body=self._clean({"name": name}))

    async def get_a_group(self, group_id: str) -> Any:
        return await self._call("GET", f"/groups/{group_id}")

    async def update_a_group(self, group_id: str, name: str | None = None) -> Any:
        return await self._call(
            "PATCH", f"/groups/{group_id}", json_body=self._clean({"name": name})
        )

    async def list_group_members(
        self,
        group_id: str,
        page_size: int | None = 30,
        page_number: int | None = None,
        next_page_token: str | None = None,
    ) -> Any:
        return await self._call(
            "GET",
            f"/groups/{group_id}/members",
            params={
                "page_size": page_size,
                "page_number": page_number,
                "next_page_token": next_page_token,
            },
        )

    async def add_group_members(self, group_id: str, members: list[dict] | None = None) -> Any:
        return await self._call(
            "POST", f"/groups/{group_id}/members", json_body=self._clean({"members": members})
        )

    async def delete_a_group_member(self, group_id: str, member_id: str) -> Any:
        return await self._call("DELETE", f"/groups/{group_id}/members/{member_id}")

    # ---- Users ----

    async def list_users(
        self,
        status: str = "active",
        page_size: int | None = 30,
        role_id: str | None = None,
        page_number: str | None = None,
        include_fields: str | None = None,
        next_page_token: str | None = None,
        license: str | None = None,
    ) -> Any:
        return await self._call(
            "GET",
            "/users",
            params={
                "status": status,
                "page_size": page_size,
                "role_id": role_id,
                "page_number": page_number,
                "include_fields": include_fields,
                "next_page_token": next_page_token,
                "license": license,
            },
        )

    async def create_users(self, action: str, user_info: dict | None = None) -> Any:
        return await self._call(
            "POST", "/users", json_body=self._clean({"action": action, "user_info": user_info})
        )

    async def check_a_user_email(self, email: str) -> Any:
        return await self._call("GET", "/users/email", params={"email": email})

    async def get_a_user(
        self,
        user_id: str,
        login_type: int | None = None,
        encrypted_email: bool | None = False,
        search_by_unique_id: bool | None = None,
    ) -> Any:
        return await self._call(
            "GET",
            f"/users/{user_id}",
            params={
                "login_type": login_type,
                "encrypted_email": encrypted_email,
                "search_by_unique_id": search_by_unique_id,
            },
        )

    async def delete_a_user(
        self,
        user_id: str,
        encrypted_email: bool | None = False,
        action: str = "disassociate",
        transfer_email: str | None = None,
        transfer_meeting: bool | None = None,
        transfer_webinar: bool | None = None,
        transfer_recording: bool | None = None,
        transfer_whiteboard: bool | None = None,
        transfer_clipfiles: bool | None = None,
        transfer_notes: bool | None = None,
        transfer_visitors: bool | None = None,
        transfer_docs: bool | None = None,
        transfer_events: bool | None = True,
    ) -> Any:
        return await self._call(
            "DELETE",
            f"/users/{user_id}",
            params={
                "encrypted_email": encrypted_email,
                "action": action,
                "transfer_email": transfer_email,
                "transfer_meeting": transfer_meeting,
                "transfer_webinar": transfer_webinar,
                "transfer_recording": transfer_recording,
                "transfer_whiteboard": transfer_whiteboard,
                "transfer_clipfiles": transfer_clipfiles,
                "transfer_notes": transfer_notes,
                "transfer_visitors": transfer_visitors,
                "transfer_docs": transfer_docs,
                "transfer_events": transfer_events,
            },
        )

    async def update_a_user(
        self,
        user_id: str,
        login_type: int | None = None,
        remove_tsp_credentials: bool | None = None,
        cms_user_id: str | None = None,
        company: str | None = None,
        custom_attributes: list[dict] | None = None,
        dept: str | None = None,
        first_name: str | None = None,
        group_id: str | None = None,
        division_ids: list[str] | None = None,
        host_key: str | None = None,
        job_title: str | None = None,
        cost_center: str | None = None,
        language: str | None = None,
        last_name: str | None = None,
        location: str | None = None,
        manager: str | None = None,
        phone_country: str | None = None,
        phone_number: str | None = None,
        phone_numbers: list[dict] | None = None,
        pmi: int | None = None,
        pronouns: str | None = None,
        pronouns_option: int | None = None,
        timezone: str | None = None,
        type: int | None = None,
        use_pmi: bool | None = False,
        vanity_name: str | None = None,
        display_name: str | None = None,
        zoom_one_type: int | None = None,
        plan_united_type: str | None = None,
        feature: dict | None = None,
        about_me: str | None = None,
        linkedin_url: str | None = None,
        license_info_list: list[dict] | None = None,
    ) -> Any:
        return await self._call(
            "PATCH",
            f"/users/{user_id}",
            params={"login_type": login_type, "remove_tsp_credentials": remove_tsp_credentials},
            json_body=self._clean(
                {
                    "cms_user_id": cms_user_id,
                    "company": company,
                    "custom_attributes": custom_attributes,
                    "dept": dept,
                    "first_name": first_name,
                    "group_id": group_id,
                    "division_ids": division_ids,
                    "host_key": host_key,
                    "job_title": job_title,
                    "cost_center": cost_center,
                    "language": language,
                    "last_name": last_name,
                    "location": location,
                    "manager": manager,
                    "phone_country": phone_country,
                    "phone_number": phone_number,
                    "phone_numbers": phone_numbers,
                    "pmi": pmi,
                    "pronouns": pronouns,
                    "pronouns_option": pronouns_option,
                    "timezone": timezone,
                    "type": type,
                    "use_pmi": use_pmi,
                    "vanity_name": vanity_name,
                    "display_name": display_name,
                    "zoom_one_type": zoom_one_type,
                    "plan_united_type": plan_united_type,
                    "feature": feature,
                    "about_me": about_me,
                    "linkedin_url": linkedin_url,
                    "license_info_list": license_info_list,
                }
            ),
        )

    async def get_user_permissions(self, user_id: str) -> Any:
        return await self._call("GET", f"/users/{user_id}/permissions")

    async def update_user_status(
        self,
        user_id: str,
        action: str,
        transfer_events: bool | None = None,
        transfer_email: str | None = None,
    ) -> Any:
        return await self._call(
            "PUT",
            f"/users/{user_id}/status",
            json_body=self._clean(
                {
                    "action": action,
                    "transfer_events": transfer_events,
                    "transfer_email": transfer_email,
                }
            ),
        )
