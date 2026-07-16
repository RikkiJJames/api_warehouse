import urllib.parse
import webbrowser
from urllib.parse import urlencode

import httpx


class GoogleHealthAuthFlow:
    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    # Google's own Health API setup guide has you register this exact fixed
    # redirect URI — there's nothing listening behind it. The auth code is
    # read by hand out of the browser's address bar after consent, unlike
    # Trakt/Spotify's local-callback-server flow. Only ever run interactively
    # from a developer machine, once, to mint the first refresh token —
    # never inside Cloud Run.
    REDIRECT_URI = "https://www.google.com"
    SCOPE = "https://www.googleapis.com/auth/googlehealth.activity_and_fitness.readonly"

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret

    def _exchange_code(self, code: str) -> dict:
        response = httpx.post(
            self.TOKEN_URL,
            data={
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        response.raise_for_status()
        return response.json()

    def run(self) -> dict:
        auth_url = self.AUTH_URL + "?" + urlencode(
            {
                "response_type": "code",
                "client_id": self.client_id,
                "redirect_uri": self.REDIRECT_URI,
                "scope": self.SCOPE,
                "access_type": "offline",
                "prompt": "consent",
            }
        )

        print("Open this URL, approve access, then you'll land on a")
        print("https://www.google.com/... page with no content — copy the")
        print("full URL from the address bar (or just the `code` param) and")
        print("paste it below:")
        print(auth_url)
        webbrowser.open(auth_url)

        pasted = input("Redirected URL or code: ").strip()
        parsed = urllib.parse.urlparse(pasted)
        query_code = urllib.parse.parse_qs(parsed.query).get("code", [None])[0]
        code = query_code or pasted

        if not code:
            raise RuntimeError("Google Health authorization failed: no code provided")

        return self._exchange_code(code)
