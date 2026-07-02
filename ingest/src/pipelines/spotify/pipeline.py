from src.pipelines.api_pipeline import ApiPipeline
from src.pipelines.spotify.authorization_flow import SpotifyAuthFlow
from src.pipelines.spotify.token_manager import TokenManager


class SpotifyPipeline(ApiPipeline):
    # cursor for me/player/recently-played — Spotify's `after` param expects a
    # Unix ms timestamp and returns only items played after it, so each run
    # only re-fetches plays that happened since the last successful run.
    WATERMARK_KEY = "recently_played_watermark"

    def __init__(self):
        super().__init__("spotify")
        self.token_manager = None

    def _persist_refresh_token(self, token: str) -> None:
        self.meta.config["refresh_token"] = token
        self.registry.update_config(self.meta.api_id, "refresh_token", token)

    def _ensure_auth(self):
        config = self.meta.config

        if config.get("refresh_token"):
            self.token_manager = TokenManager(
                client_id=config["client_id"],
                client_secret=config["client_secret"],
                refresh_token=config["refresh_token"],
                on_refresh=self._persist_refresh_token,
            )
            return

        flow = SpotifyAuthFlow(
            client_id=config["client_id"],
            client_secret=config["client_secret"],
            redirect_url=config["redirect_url"]
        )

        tokens = flow.run()

        self._persist_refresh_token(tokens["refresh_token"])

        self.token_manager = TokenManager(
            client_id=config["client_id"],
            client_secret=config["client_secret"],
            refresh_token=config["refresh_token"],
            on_refresh=self._persist_refresh_token,
        )

    def get_api_key(self):
        if self.token_manager is None:
            self._ensure_auth()

        return f"Bearer {self.token_manager.get_access_token()}"

    def get_extra_params(self) -> dict:
        watermark = self.meta.config.get(self.WATERMARK_KEY)
        if not watermark:
            return {}
        return {"recently_played": {"after": watermark}}

    async def execute(self):
        result = await super().execute()
        self._update_watermark()
        return result

    def _update_watermark(self) -> None:
        max_played_at = self.registry.get_max_value("spotify.recently_played", "played_at")
        if max_played_at is None:
            return
        epoch_ms = str(int(max_played_at.timestamp() * 1000))
        self.meta.config[self.WATERMARK_KEY] = epoch_ms
        self.registry.update_config(self.meta.api_id, self.WATERMARK_KEY, epoch_ms)