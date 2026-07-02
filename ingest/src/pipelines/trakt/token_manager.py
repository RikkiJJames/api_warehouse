import time

import httpx


class TraktAuthError(Exception):
    pass


class TraktTokenManager:
    TOKEN_URL = "https://api.trakt.tv/oauth/token"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        timeout: int = 10,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.timeout = timeout

        self._access_token: str | None = None
        self._expires_at: float = 0

    def _is_expired(self) -> bool:
        return time.time() >= self._expires_at

    def _refresh_access_token(self) -> None:
        response = httpx.post(
            self.TOKEN_URL,
            json={
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token",
            },
            timeout=self.timeout,
        )

        if response.status_code != 200:
            raise TraktAuthError(response.text)

        payload = response.json()

        self._access_token = payload["access_token"]
        if "refresh_token" in payload:
            self.refresh_token = payload["refresh_token"]
        expires_in = payload.get("expires_in", 7776000)
        self._expires_at = time.time() + expires_in - 300

    def get_access_token(self) -> str:
        if self._access_token is None or self._is_expired():
            self._refresh_access_token()
        return self._access_token
