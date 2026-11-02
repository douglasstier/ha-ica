"""Minimal async client for ICA's (unofficial) shopping list API."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from typing import Any

import aiohttp

from .const import API_BASE, USER_INFO_URL

_LOGGER = logging.getLogger(__name__)


class IcaAuthError(Exception):
    """The thSessionId cookie is no longer valid."""


class IcaApiError(Exception):
    """Any other API failure."""


class IcaApi:
    """Talks to ica.se. Auth: thSessionId cookie -> short-lived bearer token."""

    def __init__(self, session: aiohttp.ClientSession, session_id: str) -> None:
        self._session = session
        self._session_id = session_id
        self._token: str | None = None
        self._token_expires = datetime.min.replace(tzinfo=timezone.utc)
        self.customer_id: int | None = None
        self.first_name: str | None = None

    async def _get_token(self, force: bool = False) -> str:
        now = datetime.now(timezone.utc)
        if not force and self._token and now < self._token_expires - timedelta(seconds=30):
            return self._token
        try:
            async with self._session.get(
                USER_INFO_URL,
                headers={"Cookie": f"thSessionId={self._session_id}", "Accept": "application/json"},
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status in (401, 403):
                    raise IcaAuthError
                if resp.status != 200:
                    raise IcaApiError(f"user/information returned {resp.status}")
                data = await resp.json(content_type=None)
        except aiohttp.ClientError as err:
            raise IcaApiError(str(err)) from err
        token = data.get("accessToken")
        # loginState 2 = logged in. Anything else means the cookie is anonymous/expired.
        if not token or data.get("loginState") != 2:
            raise IcaAuthError
        self._token = token
        self.customer_id = data.get("customerId")
        self.first_name = data.get("firstName")
        try:
            self._token_expires = datetime.fromisoformat(data["tokenExpires"][:26].rstrip("Z") + "+00:00")
        except (KeyError, ValueError):
            self._token_expires = now + timedelta(minutes=3)
        return token

    async def _request(self, method: str, path: str, json: Any = None, retry: bool = True) -> Any:
        token = await self._get_token()
        try:
            async with self._session.request(
                method,
                f"{API_BASE}{path}",
                json=json,
                headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status == 401 and retry:
                    await self._get_token(force=True)
                    return await self._request(method, path, json, retry=False)
                if resp.status == 401:
                    raise IcaAuthError
                if resp.status >= 300:
                    raise IcaApiError(f"{method} {path} returned {resp.status}: {await resp.text()}")
                text = await resp.text()
                if not text:
                    return None
                try:
                    return await resp.json(content_type=None)
                except ValueError:
                    return text
        except aiohttp.ClientError as err:
            raise IcaApiError(str(err)) from err

    async def validate(self) -> None:
        await self._get_token(force=True)

    async def get_lists(self) -> list[dict]:
        data = await self._request("GET", "/list/all")
        if isinstance(data, dict) and "items" in data:
            return data["items"]
        return data or []

    async def add_row(self, list_id: str, text: str) -> None:
        await self._request("POST", f"/list/{list_id}/row", {"text": text})

    async def update_row(self, row: dict, **changes: Any) -> None:
        body = {**row, **changes, "updated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}
        await self._request("PUT", f"/row/{row['id']}", body)

    async def delete_row(self, row_id: str) -> None:
        await self._request("DELETE", f"/row/{row_id}")
