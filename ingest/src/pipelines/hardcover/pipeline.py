from src.api.execution_client import ExecutionClient
from src.api.execution_engine import ExecutionEngine
from src.pipelines.api_pipeline import ApiPipeline


class HardcoverPipeline(ApiPipeline):
    # Hardcover's GraphQL schema scopes `user_books` by an explicit user_id
    # rather than an implicit "me" filter, so the id is resolved once via a
    # `me` query and cached in api_config (mirrors TraktPipeline's refresh_token caching).
    ME_QUERY = "query Me { me { id } }"

    def __init__(self):
        super().__init__("hardcover")

    def get_api_key(self) -> str:
        token = self.meta.config["api_token"]
        return token if token.startswith("Bearer ") else f"Bearer {token}"

    async def _ensure_user_id(self, client: ExecutionClient) -> int:
        cached = self.meta.config.get("user_id")
        if cached:
            return int(cached)

        response = await client.post_endpoint("", query=self.ME_QUERY)
        me = (response.get("data") or {}).get("me")
        # Hasura-generated root fields return an array even for a single row.
        user = me[0] if isinstance(me, list) else me
        if not user or "id" not in user:
            raise RuntimeError(f"Could not resolve Hardcover user id from response: {response}")

        user_id = user["id"]
        self.meta.config["user_id"] = str(user_id)
        self.registry.update_config(self.meta.api_id, "user_id", str(user_id))
        return user_id

    def get_extra_params(self) -> dict:
        user_id = int(self.meta.config["user_id"])
        return {
            "read_books": {"user_id": user_id},
            "currently_reading": {"user_id": user_id},
            "want_to_read": {"user_id": user_id},
        }

    async def execute(self):
        async with ExecutionClient(
            base_url=self.meta.api.base_url,
            api_key=self.get_api_key(),
            auth_header=self.get_auth_header(),
        ) as client:
            await self._ensure_user_id(client)

            engine = ExecutionEngine(
                api=client,
                registry=self.registry,
                api_id=self.meta.api_id,
            )
            return await engine.run(self.meta.endpoints, extra_params=self.get_extra_params())
