import base64

import httpx


class ZoomError(Exception):
    def __init__(self, message: str):
        super().__init__(f"Zoom API error: {message}")


class ZoomClient:
    """Async httpx client wrapping Zoom's Users Admin API.

    Auth is Server-to-Server OAuth (the "account_credentials" grant —
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

    async def create_user(
        self,
        email: str,
        user_type: int = 1,
        action: str = "create",
        display_name: str | None = None,
        division_ids: list[str] | None = None,
    ) -> object:
        user_info = self._clean(
            {
                "email": email,
                "type": user_type,
                "display_name": display_name,
                "division_ids": division_ids,
            }
        )
        body = {"action": action, "user_info": user_info}
        return await self._call("POST", "/users", json_body=body)

    async def check_user_email(self, email: str) -> object:
        return await self._call("GET", "/users/email", params={"email": email})

    async def get_user(self, user_id: str, login_type: int | None = None) -> object:
        return await self._call("GET", f"/users/{user_id}", params={"login_type": login_type})

    async def add_group_member(
        self, group_id: str, email: str | None = None, user_id: str | None = None
    ) -> object:
        member = self._clean({"email": email, "id": user_id})
        return await self._call(
            "POST", f"/groups/{group_id}/members", json_body={"members": [member]}
        )

    async def list_groups(self) -> object:
        return await self._call("GET", "/groups")
