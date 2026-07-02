from src.pipelines.api_pipeline import ApiPipeline
from src.pipelines.spotify.authorization_flow import SpotifyAuthFlow
from src.pipelines.spotify.token_manager import TokenManager


class SpotifyPipeline(ApiPipeline):

    def __init__(self):
        super().__init__("spotify")
        self.token_manager = None

    def _ensure_auth(self):
        config = self.meta.config

        if config.get("refresh_token"):
            self.token_manager = TokenManager(
                client_id=config["client_id"],
                client_secret=config["client_secret"],
                refresh_token=config["refresh_token"],
            )
            return

        flow = SpotifyAuthFlow(
            client_id=config["client_id"],
            client_secret=config["client_secret"],
            redirect_url=config["redirect_url"]
        )

        tokens = flow.run()

        config["refresh_token"] = tokens["refresh_token"]

        self.token_manager = TokenManager(
            client_id=config["client_id"],
            client_secret=config["client_secret"],
            refresh_token=config["refresh_token"],
        )

    def get_api_key(self):
        if self.token_manager is None:
            self._ensure_auth()

        return f"Bearer {self.token_manager.get_access_token()}"