import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Raised when a 429 can't be recovered from (retries exhausted or the
    Retry-After wait is too long to block on) — callers should stop making
    further requests rather than keep hammering an already-limited API."""

    def __init__(self, endpoint: str, retry_after: float):
        self.endpoint = endpoint
        self.retry_after = retry_after
        super().__init__(f"Rate limited on {endpoint} (retry_after={retry_after}s)")


class GraphQLError(Exception):
    """Raised when a GraphQL response's top-level `errors` array is non-empty
    — GraphQL APIs return HTTP 200 even when the query itself failed, so this
    has to be checked explicitly instead of relying on raise_for_status()."""

    def __init__(self, endpoint: str, errors: list):
        self.errors = errors
        super().__init__(f"GraphQL errors from {endpoint or '<base_url>'}: {errors}")


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
        await asyncio.sleep(delay)

    async def get_endpoint(
        self,
        endpoint: str,
        params: dict | None = None,
        max_retries: int = 3,
        max_retry_after: float = 60,
    ) -> dict | list:
        logger.info(f"GET {endpoint}")

        merged = dict(self.default_params)
        if self.auth_mode == "query_param":
            merged["api_key"] = self.api_key
        if params:
            merged.update(params)

        for attempt in range(max_retries + 1):
            # 🔥 IMPORTANT: detect full URLs (Spotify pagination)
            if endpoint.startswith("http"):
                response = await httpx.AsyncClient(
                    headers=self.client.headers,
                    timeout=self.client.timeout,
                ).get(endpoint)
            else:
                response = await self.client.get(endpoint, params=merged)

            if response.status_code == 429:
                retry_after = float(response.headers.get("Retry-After", 1))

                # Don't block the whole pipeline run on a long cooldown, and
                # don't keep retrying once attempts are exhausted — raise so
                # the caller can stop hitting this (already-limited) API.
                if attempt >= max_retries or retry_after > max_retry_after:
                    logger.warning(
                        f"429 from {endpoint}; giving up "
                        f"(retry_after={retry_after}s, attempt={attempt + 1}/{max_retries + 1})"
                    )
                    raise RateLimitExceeded(endpoint, retry_after)

                logger.warning(
                    f"429 from {endpoint}, retrying in {retry_after}s "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                await asyncio.sleep(retry_after)
                continue

            response.raise_for_status()
            self._pagination = {
                "page_count": int(response.headers.get("X-Pagination-Page-Count", 1)),
                "item_count": int(response.headers.get("X-Pagination-Item-Count", 0)),
            }
            return response.json()

    async def post_endpoint(
        self,
        endpoint: str,
        query: str,
        variables: dict | None = None,
        max_retries: int = 3,
        max_retry_after: float = 60,
    ) -> dict:
        logger.info(f"POST {endpoint or self.base_url}")

        payload = {"query": query, "variables": variables or {}}

        for attempt in range(max_retries + 1):
            response = await self.client.post(endpoint, json=payload)

            if response.status_code == 429:
                retry_after = float(response.headers.get("Retry-After", 1))

                if attempt >= max_retries or retry_after > max_retry_after:
                    logger.warning(
                        f"429 from {endpoint}; giving up "
                        f"(retry_after={retry_after}s, attempt={attempt + 1}/{max_retries + 1})"
                    )
                    raise RateLimitExceeded(endpoint, retry_after)

                logger.warning(
                    f"429 from {endpoint}, retrying in {retry_after}s "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                await asyncio.sleep(retry_after)
                continue

            response.raise_for_status()
            body = response.json()

            if body.get("errors"):
                raise GraphQLError(endpoint, body["errors"])

            self._pagination = {"page_count": 1, "item_count": 0}
            return body