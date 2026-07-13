from datetime import timezone

from src.api.execution_client import ExecutionClient
from src.api.execution_engine import ExecutionEngine
from src.pipelines.api_pipeline import ApiPipeline
from src.pipelines.trakt.authorization_flow import TraktAuthFlow
from src.pipelines.trakt.token_manager import TraktTokenManager


class TraktPipeline(ApiPipeline):
    # Watermarks for users/me/history/{movies,episodes} — Trakt's `start_at`
    # param (ISO 8601) returns only history entries at/after that timestamp,
    # so each run only re-fetches watch events since the last successful run
    # instead of re-downloading the full history every time.
    WATCHED_MOVIES_WATERMARK_KEY = "watched_movies_watermark"
    WATCHED_EPISODES_WATERMARK_KEY = "watched_episodes_watermark"

    def __init__(self):
        super().__init__("trakt")
        self.token_manager = None

    def _persist_refresh_token(self, token: str) -> None:
        self.meta.config["refresh_token"] = token
        self.registry.update_config(self.meta.api_id, "refresh_token", token)

    def _ensure_auth(self):
        config = self.meta.config

        if config.get("refresh_token"):
            self.token_manager = TraktTokenManager(
                client_id=config["client_id"],
                client_secret=config["client_secret"],
                refresh_token=config["refresh_token"],
                redirect_url=config["redirect_url"],
                on_refresh=self._persist_refresh_token,
            )
            return

        flow = TraktAuthFlow(
            client_id=config["client_id"],
            client_secret=config["client_secret"],
            redirect_url=config["redirect_url"],
        )

        tokens = flow.run()
        self._persist_refresh_token(tokens["refresh_token"])

        self.token_manager = TraktTokenManager(
            client_id=config["client_id"],
            client_secret=config["client_secret"],
            refresh_token=config["refresh_token"],
            redirect_url=config["redirect_url"],
            on_refresh=self._persist_refresh_token,
        )

    def get_api_key(self) -> str:
        if self.token_manager is None:
            self._ensure_auth()
        return f"Bearer {self.token_manager.get_access_token()}"

    def get_extra_headers(self) -> dict:
        return {
            "trakt-api-key": self.meta.config["client_id"],
            "trakt-api-version": "2",
        }

    def get_extra_params(self) -> dict:
        params = {}

        movies_watermark = self.meta.config.get(self.WATCHED_MOVIES_WATERMARK_KEY)
        if movies_watermark:
            params["watched_movies"] = {"start_at": movies_watermark}

        episodes_watermark = self.meta.config.get(self.WATCHED_EPISODES_WATERMARK_KEY)
        if episodes_watermark:
            params["watched_episodes"] = {"start_at": episodes_watermark}

        return params

    async def execute(self):
        async with ExecutionClient(
            base_url=self.meta.api.base_url,
            api_key=self.get_api_key(),
            auth_header=self.get_auth_header(),
            extra_headers=self.get_extra_headers(),
        ) as client:
            engine = ExecutionEngine(
                api=client,
                registry=self.registry,
                api_id=self.meta.api_id,
            )
            result = await engine.run(self.meta.endpoints, extra_params=self.get_extra_params())
            self._update_watermarks()
            return result

    def _update_watermarks(self) -> None:
        self._update_watermark(
            "trakt.watched_movies", "watched_at", self.WATCHED_MOVIES_WATERMARK_KEY
        )
        self._update_watermark(
            "trakt.watched_episodes", "watched_at", self.WATCHED_EPISODES_WATERMARK_KEY
        )

    def _update_watermark(self, schema_table: str, column: str, config_key: str) -> None:
        max_watched_at = self.registry.get_max_value(schema_table, column)
        if max_watched_at is None:
            return
        if max_watched_at.tzinfo is not None:
            max_watched_at = max_watched_at.astimezone(timezone.utc)
        start_at = max_watched_at.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        self.meta.config[config_key] = start_at
        self.registry.update_config(self.meta.api_id, config_key, start_at)
