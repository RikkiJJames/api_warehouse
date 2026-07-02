import time
import base64
import httpx


class SpotifyAuthError(Exception):
    pass


class TokenManager:
    TOKEN_URL = "https://accounts.spotify.com/api/token"

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

    def _basic_auth_header(self) -> str:
        creds = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(creds.encode()).decode()
        return f"Basic {encoded}"

    def _is_expired(self) -> bool:
        return time.time() >= self._expires_at

    def _refresh_access_token(self) -> None:
        response = httpx.post(
            self.TOKEN_URL,
            headers={
                "Authorization": self._basic_auth_header(),
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
            },
            timeout=self.timeout,
        )

        if response.status_code != 200:
            raise SpotifyAuthError(response.text)

        payload = response.json()

        self._access_token = payload["access_token"]
        expires_in = payload.get("expires_in", 3600)
        self._expires_at = time.time() + expires_in - 30

    def get_access_token(self) -> str:
        if self._access_token is None or self._is_expired():
            self._refresh_access_token()

        return self._access_token

    def force_refresh(self) -> str:
        self._refresh_access_token()
        return self._access_token