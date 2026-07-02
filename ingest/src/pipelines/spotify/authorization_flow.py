import base64
import http.server
import threading
import urllib.parse
import webbrowser
from urllib.parse import urlencode
import httpx


class SpotifyAuthFlow:
    SCOPES = "user-read-recently-played user-top-read user-library-read"

    def __init__(self, client_id: str, client_secret: str, redirect_url: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_url
        parsed_port = urllib.parse.urlparse(redirect_url).port
        if parsed_port is None:
            raise ValueError(f"No port found in redirect_url: {redirect_url}")
        self.port = parsed_port

        self._auth_code = None
        self._done = threading.Event()

    class _CallbackHandler(http.server.BaseHTTPRequestHandler):
        parent = None

        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)

            if "code" in params:
                self.parent._auth_code = params["code"][0]

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"You can close this tab.")
            self.parent._done.set()

        def log_message(self, *args):
            pass

    def _exchange_code(self, code: str) -> dict:
        creds = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        response = httpx.post(
            "https://accounts.spotify.com/api/token",
            headers={"Authorization": f"Basic {creds}"},
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.redirect_uri,
            },
        )
        response.raise_for_status()
        return response.json()

    def run(self) -> dict:
        auth_url = "https://accounts.spotify.com/authorize?" + urlencode(
            {
                "client_id": self.client_id,
                "response_type": "code",
                "redirect_uri": self.redirect_uri,
                "scope": self.SCOPES,
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
            raise RuntimeError("Authorization failed")

        return self._exchange_code(self._auth_code)