from src.api.execution_client import ExecutionClient
from src.api.execution_engine import ExecutionEngine
from src.pipelines.api_pipeline import ApiPipeline
from src.pipelines.trakt.authorization_flow import TraktAuthFlow
from src.pipelines.trakt.token_manager import TraktTokenManager


class TraktPipeline(ApiPipeline):

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
            return await engine.run(self.meta.endpoints)
