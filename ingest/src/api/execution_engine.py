import asyncio
import logging
import re

from src.api.execution_client import ExecutionClient
from src.api.execution_context import ExecutionContext
from src.api.resolver import Resolver
from src.api.response_extractor import ResponseExtractor
from src.api.storage_adapter import StorageAdapter
from src.core.api_registry import ApiRegistry


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

        # First request
        logger.info("Retrieving Page 1")
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

        # Header-based pagination (Trakt): page param increments
        if total_pages > 1:
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

    async def run(self, endpoints: list[dict]) -> dict:
        results = {}

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

            try:
                if db_params:
                    p = db_params[0]

                    source_values = self.registry.get_source_values(
                        p["source_table"],
                        p["source_column"],
                        distinct=p.get("is_distinct", False),
                    )

                    total = 0

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