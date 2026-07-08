import asyncio
import logging
import re

from src.api.execution_client import ExecutionClient, RateLimitExceeded
from src.api.execution_context import ExecutionContext
from src.api.resolver import Resolver
from src.api.response_extractor import ResponseExtractor
from src.api.storage_adapter import StorageAdapter
from src.core.api_registry import ApiRegistry


# Conservative across Spotify's batch endpoints — /albums caps at 20 ids per
# request, /tracks and /artists at 50.
BATCH_SIZE = 20


def _extract_field(records: list, field: str) -> list:
    if not records:
        return []
    if not isinstance(records[0], dict):
        return list(records)
    return [r[field] for r in records if isinstance(r, dict) and field in r]


logger = logging.getLogger(__name__)

class ExecutionEngine:
    def __init__(self, api, registry, api_id=None):
        self.api = api
        self.registry = registry
        self.api_id = api_id

        self.context = ExecutionContext()
        self.resolver = Resolver(self.context)
        self.extractor = ResponseExtractor()
        self.storage = StorageAdapter(registry, api_id)

    async def process_endpoint(
        self,
        endpoint: dict,
        path: str,
        params: dict | None = None,
        extra: dict | None = None,
    ):
        all_items = []
        limit = int((params or {}).get("limit", 50))
        is_graphql = endpoint.get("method") == "POST"

        # First request
        logger.info("Retrieving Page 1")
        if is_graphql:
            # GraphQL variables are type-checked against the schema (Int vs
            # String), unlike REST query params — limit/offset must be ints,
            # not the raw string default_values config stores everything as.
            variables = {**(params or {}), "limit": limit, "offset": int((params or {}).get("offset", 0))}
            raw = await self.api.post_endpoint(path, query=endpoint["query"], variables=variables)
        else:
            raw = await self.api.get_endpoint(path, params=params)
        total_pages = self.api._pagination.get("page_count", 1)
        item_count = self.api._pagination.get("item_count", 0)

        items = self.extractor.extract(raw, endpoint.get("response_path"))
        if not items:
            logger.info("No items found")
            if not endpoint.get("db_target"):
                self.context.store(endpoint["logical_name"], [])
            return []

        all_items.extend(items)
        logger.info(f"Fetched {len(items)} items from {path} (page 1/{total_pages}, total={item_count})")
        self.storage.save(endpoint, endpoint["logical_name"], items, extra)

        # Offset-based pagination (GraphQL, e.g. Hardcover): keep requesting
        # while a full page came back, since there's no total-count/next-link
        # signal to rely on generically across GraphQL APIs.
        if is_graphql:
            offset = limit
            while len(items) == limit:
                logger.info(f"Retrieving offset {offset}")
                page_variables = {**(params or {}), "limit": limit, "offset": offset}
                raw = await self.api.post_endpoint(path, query=endpoint["query"], variables=page_variables)
                items = self.extractor.extract(raw, endpoint.get("response_path"))
                if not items:
                    break
                all_items.extend(items)
                logger.info(f"Fetched {len(items)} items from {path} (offset {offset})")
                self.storage.save(endpoint, endpoint["logical_name"], items, extra)
                offset += limit

        # Header-based pagination (Trakt): page param increments
        elif total_pages > 1:
            for page in range(2, total_pages + 1):
                logger.info(f"Retrieving Page {page}/{total_pages}")
                raw = await self.api.get_endpoint(path, params={**(params or {}), "page": page})
                items = self.extractor.extract(raw, endpoint.get("response_path"))
                if not items:
                    break
                all_items.extend(items)
                logger.info(f"Fetched {len(items)} items from {path} (page {page}/{total_pages})")
                self.storage.save(endpoint, endpoint["logical_name"], items, extra)

        # URL-based pagination (Spotify): follow next links
        else:
            next_url = raw.get("next") if isinstance(raw, dict) else None
            page = 2
            while next_url and len(items) >= limit:
                logger.info(f"Retrieving Page {page}")
                raw = await self.api.get_endpoint(next_url)
                items = self.extractor.extract(raw, endpoint.get("response_path"))
                if not items:
                    break
                all_items.extend(items)
                logger.info(f"Fetched {len(items)} items from {next_url}")
                self.storage.save(endpoint, endpoint["logical_name"], items, extra)
                next_url = raw.get("next") if isinstance(raw, dict) else None
                page += 1

        if not endpoint.get("db_target"):
            self.context.store(endpoint["logical_name"], all_items)
        return all_items

    async def run(self, endpoints: list[dict], extra_params: dict[str, dict] | None = None) -> dict:
        results = {}
        extra_params = extra_params or {}

        for endpoint in sorted(endpoints, key=lambda x: x["exec_order"]):

            logical_name = endpoint["logical_name"]
            template = endpoint["path_template"]

            params = self.registry.get_endpoint_params(endpoint["id"])

            db_params = [p for p in params if p.get("source_table")]
            static_params = {
                p["param_name"]: p["default_value"]
                for p in params
                if p.get("default_value") and not p.get("source_table")
            }
            static_params.update(extra_params.get(logical_name, {}))

            try:
                if db_params:
                    p = db_params[0]

                    source_values = self.registry.get_source_values(
                        p["source_table"],
                        p["source_column"],
                        distinct=p.get("is_distinct", False),
                    )

                    total = 0

                    # Some endpoints (e.g. Spotify's /tracks, /albums, /artists) accept
                    # a batch of comma-separated ids per request instead of one id per
                    # call — batching avoids hammering the API with hundreds of requests
                    # as the source table (e.g. recently_played) grows over time.
                    if p["param_name"] == "ids":
                        new_values = source_values
                        if endpoint.get("db_target"):
                            # This metadata (track/album/artist) never changes once
                            # fetched, so skip ids we've already stored instead of
                            # re-requesting the whole historical set every run.
                            existing_ids = set(
                                self.registry.get_source_values(
                                    endpoint["db_target"], p["source_column"]
                                )
                            )
                            new_values = [v for v in source_values if v not in existing_ids]

                        if not new_values:
                            print(f"{logical_name} → 0 (nothing new)")
                            results[logical_name] = {"status": "ok", "count": 0}
                            continue

                        batches = [
                            new_values[i : i + BATCH_SIZE]
                            for i in range(0, len(new_values), BATCH_SIZE)
                        ]
                        for i, batch in enumerate(batches):
                            if i > 0:
                                await self.api.throttle()

                            path = self.resolver.resolve(template)

                            try:
                                items = await self.process_endpoint(
                                    endpoint,
                                    path,
                                    params={**static_params, p["param_name"]: ",".join(batch)},
                                )
                                total += len(items)
                                print(f"{logical_name}[batch {i + 1}/{len(batches)}] → {len(items)}")
                            except RateLimitExceeded as e:
                                # Rate limiting is API-wide, not per-batch — every
                                # remaining batch would just 429 too, so stop here
                                # instead of burning through the rest.
                                logger.warning(
                                    f"{logical_name} rate-limited on batch {i + 1}/{len(batches)} "
                                    f"({e}); skipping remaining batches"
                                )
                                break
                            except Exception as e:
                                logger.warning(f"{logical_name}[batch {i + 1}/{len(batches)}] failed: {e}")

                        results[logical_name] = {"status": "ok", "count": total}
                        continue

                    for i, value in enumerate(source_values):
                        if i > 0:
                            await self.api.throttle()

                        path = self.resolver.resolve(template)

                        try:
                            items = await self.process_endpoint(
                                endpoint,
                                path,
                                params={**static_params, p["param_name"]: value},
                                extra={p["param_name"]: value},
                            )
                            total += len(items)
                            print(f"{logical_name}[{value}] → {len(items)}")
                        except RateLimitExceeded as e:
                            logger.warning(
                                f"{logical_name} rate-limited on [{value}] ({e}); "
                                f"skipping remaining values"
                            )
                            break
                        except Exception as e:
                            logger.warning(f"{logical_name}[{value}] failed: {e}")

                    results[logical_name] = {"status": "ok", "count": total}

                else:
                    path = self.resolver.resolve(template)

                    items = await self.process_endpoint(
                        endpoint,
                        path,
                        params=static_params or None,
                        extra=static_params or None,
                    )

                    results[logical_name] = {
                        "status": "ok",
                        "count": len(items),
                    }

                    print(f"{logical_name} → {len(items)}")

            except Exception as e:
                logger.error(f"{logical_name} failed: {e}")
                results[logical_name] = {"status": "error", "error": str(e)}

        return results