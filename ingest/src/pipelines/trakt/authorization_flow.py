import base64
import hashlib
import http.server
import logging
import secrets
import threading
import urllib.parse
import webbrowser
from urllib.parse import urlencode

import httpx

logger = logging.getLogger(__name__)


class TraktAuthFlow:
    AUTH_URL = "https://trakt.tv/oauth/authorize"
    TOKEN_URL = "https://api.trakt.tv/oauth/token"

    def __init__(self, client_id: str, redirect_url: str):
        self.client_id = client_id
        self.redirect_uri = redirect_url
        parsed_port = urllib.parse.urlparse(redirect_url).port
        if parsed_port is None:
            raise ValueError(f"No port found in redirect_url: {redirect_url}")
        self.port = parsed_port

        # PKCE (RFC 7636): a per-run random verifier whose S256 hash goes in
        # the authorize URL, then the verifier itself is sent on the code
        # exchange in place of a client_secret.
        self.code_verifier = secrets.token_urlsafe(64)
        self.code_challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(self.code_verifier.encode()).digest())
            .rstrip(b"=")
            .decode()
        )

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
                "code_verifier": self.code_verifier,
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
                "code_challenge": self.code_challenge,
                "code_challenge_method": "S256",
            }
        )

        handler = self._CallbackHandler
        handler.parent = self

        server = http.server.HTTPServer(("localhost", self.port), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        logger.info(f"Open this URL to authorize Trakt: {auth_url}")
        webbrowser.open(auth_url)

        self._done.wait()
        server.shutdown()

        if not self._auth_code:
            raise RuntimeError("Trakt authorization failed: no code received")

        return self._exchange_code(self._auth_code)
