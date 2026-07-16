import time
from typing import Callable

import httpx


class GoogleHealthAuthError(Exception):
    pass


class GoogleHealthTokenManager:
    TOKEN_URL = "https://oauth2.googleapis.com/token"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        timeout: int = 10,
        on_refresh: Callable[[str], None] | None = None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.timeout = timeout
        self.on_refresh = on_refresh

        self._access_token: str | None = None
        self._expires_at: float = 0

    def _is_expired(self) -> bool:
        return time.time() >= self._expires_at

    def _refresh_access_token(self) -> None:
        # Google's token endpoint expects form-encoded data (RFC 6749), not
        # a JSON body like Trakt's.
        response = httpx.post(
            self.TOKEN_URL,
            data={
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token",
            },
            timeout=self.timeout,
        )

        if response.status_code != 200:
            raise GoogleHealthAuthError(response.text)

        payload = response.json()

        self._access_token = payload["access_token"]
        # Google doesn't normally rotate refresh tokens on a plain refresh,
        # but handle it the same way as Trakt in case that ever changes.
        if "refresh_token" in payload and payload["refresh_token"] != self.refresh_token:
            self.refresh_token = payload["refresh_token"]
            if self.on_refresh:
                self.on_refresh(self.refresh_token)
        expires_in = payload.get("expires_in", 3600)
        self._expires_at = time.time() + expires_in - 300

    def get_access_token(self) -> str:
        if self._access_token is None or self._is_expired():
            self._refresh_access_token()
        return self._access_token
