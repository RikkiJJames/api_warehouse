import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class ExecutionClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        auth_header: str = "x-apisports-key",
        auth_mode: str = "header",
        default_params: dict | None = None,
        extra_headers: dict | None = None,
        timeout: int = 10,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.auth_mode = auth_mode
        self.default_params = default_params or {}

        headers = {} if auth_mode == "query_param" else {auth_header: api_key}
        headers.update(extra_headers or {})

        self._pagination: dict = {}

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=timeout,
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        await self.client.aclose()

    async def throttle(self, delay: float = 0.1):
        import asyncio
        await asyncio.sleep(delay)

    async def get_endpoint(self, endpoint: str, params: dict | None = None) -> dict | list:
        logger.info(f"GET {endpoint}")

        merged = dict(self.default_params)
        if self.auth_mode == "query_param":
            merged["api_key"] = self.api_key
        if params:
            merged.update(params)

        # 🔥 IMPORTANT: detect full URLs (Spotify pagination)
        if endpoint.startswith("http"):
            response = await httpx.AsyncClient(
                headers=self.client.headers,
                timeout=self.client.timeout,
            ).get(endpoint)
        else:
            response = await self.client.get(endpoint, params=merged)

        response.raise_for_status()
        self._pagination = {
            "page_count": int(response.headers.get("X-Pagination-Page-Count", 1)),
            "item_count": int(response.headers.get("X-Pagination-Item-Count", 0)),
        }
        return response.json()