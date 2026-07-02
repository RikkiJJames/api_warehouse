import http.server
import threading
import urllib.parse
import webbrowser
from urllib.parse import urlencode

import httpx


class TraktAuthFlow:
    AUTH_URL = "https://trakt.tv/oauth/authorize"
    TOKEN_URL = "https://api.trakt.tv/oauth/token"

    def __init__(self, client_id: str, client_secret: str, redirect_url: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_url
        parsed_port = urllib.parse.urlparse(redirect_url).port
        if parsed_port is None:
            raise ValueError(f"No port found in redirect_url: {redirect_url}")
        self.port = parsed_port

        self._auth_code: str | None = None
        self._done = threading.Event()

    class _CallbackHandler(http.server.BaseHTTPRequestHandler):
        parent: "TraktAuthFlow"

        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)

            if "code" in params:
                self.parent._auth_code = params["code"][0]

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"You can close this tab.")
            self.parent._done.set()

        def log_message(self, format, *args):  # noqa: A002
            pass

    def _exchange_code(self, code: str) -> dict:
        response = httpx.post(
            self.TOKEN_URL,
            json={
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri,
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
                "redirect_uri": self.redirect_uri,
            }
        )

        handler = self._CallbackHandler
        handler.parent = self

        server = http.server.HTTPServer(("localhost", self.port), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        webbrowser.open(auth_url)

        self._done.wait()
        server.shutdown()

        if not self._auth_code:
            raise RuntimeError("Trakt authorization failed: no code received")

        return self._exchange_code(self._auth_code)
