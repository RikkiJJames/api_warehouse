from datetime import date, datetime, timedelta, timezone

from src.api.execution_client import ExecutionClient
from src.api.execution_engine import ExecutionEngine
from src.pipelines.api_pipeline import ApiPipeline
from src.pipelines.google_health.authorization_flow import GoogleHealthAuthFlow
from src.pipelines.google_health.token_manager import GoogleHealthTokenManager


class GoogleHealthPipeline(ApiPipeline):
    # dailyRollUp's range is a closed-open interval, so re-including the
    # last finalized day (instead of starting strictly after it) makes each
    # run re-touch it — otherwise a day whose sync was still trickling in
    # when we last fetched it would never be revisited to pick up the rest.
    WATERMARK_OVERLAP_DAYS = 1
    # ~3 years — comfortably under dailyRollUp's 10k-point-per-page limit
    # for a single request, so no pagination handling is needed.
    INITIAL_LOOKBACK_DAYS = 1095

    DATA_TYPES = ["steps", "distance", "total-calories", "active-minutes"]

    def __init__(self):
        super().__init__("google_health")
        self.token_manager = None

    def _persist_refresh_token(self, token: str) -> None:
        self.meta.config["refresh_token"] = token
        self.registry.update_config(self.meta.api_id, "refresh_token", token)

    def _ensure_auth(self):
        config = self.meta.config

        if not config.get("refresh_token"):
            # Can't run interactively inside Cloud Run — the refresh_token
            # secret must already be populated (via a one-off local run of
            # this flow) before this pipeline is ever deployed.
            flow = GoogleHealthAuthFlow(
                client_id=config["client_id"],
                client_secret=config["client_secret"],
            )
            tokens = flow.run()
            self._persist_refresh_token(tokens["refresh_token"])

        self.token_manager = GoogleHealthTokenManager(
            client_id=config["client_id"],
            client_secret=config["client_secret"],
            refresh_token=config["refresh_token"],
            on_refresh=self._persist_refresh_token,
        )

    def get_api_key(self) -> str:
        if self.token_manager is None:
            self._ensure_auth()
        return f"Bearer {self.token_manager.get_access_token()}"

    def get_extra_params(self) -> dict:
        today = datetime.now(timezone.utc).date()
        params = {}

        for data_type in self.DATA_TYPES:
            logical_name = data_type.replace("-", "_")
            watermark = self.meta.config.get(f"{logical_name}_watermark")

            if watermark:
                start = date.fromisoformat(watermark) - timedelta(days=self.WATERMARK_OVERLAP_DAYS)
            else:
                start = today - timedelta(days=self.INITIAL_LOOKBACK_DAYS)

            # end is exclusive, so +1 day includes today.
            end = today + timedelta(days=1)

            params[logical_name] = {
                "range": {
                    "start": {"year": start.year, "month": start.month, "day": start.day},
                    "end": {"year": end.year, "month": end.month, "day": end.day},
                },
                "windowSizeDays": 1,
            }

        return params

    async def execute(self):
        async with ExecutionClient(
            base_url=self.meta.api.base_url,
            api_key=self.get_api_key(),
            auth_header=self.get_auth_header(),
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
        today = datetime.now(timezone.utc).date().isoformat()
        for data_type in self.DATA_TYPES:
            logical_name = data_type.replace("-", "_")
            watermark_key = f"{logical_name}_watermark"
            self.meta.config[watermark_key] = today
            self.registry.update_config(self.meta.api_id, watermark_key, today)
