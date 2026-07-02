import asyncio

from src.api.execution_client import ExecutionClient
from src.api.execution_engine import ExecutionEngine
from src.bootstrap.run_seed import run_seed
from src.core.api_registry import ApiRegistry
from src.core.api_client import ApiClient
from src.services.api_service import get_service


class ApiPipeline:
    def __init__(self, api_name: str):
        self.api_name = api_name
        self.service = None
        self.registry = None
        self.meta = None

    def bootstrap(self):
        run_seed(self.api_name, service=self.service)

    def load_metadata(self):
        self.registry = ApiRegistry(self.service)
        self.meta = ApiClient(
            api_name=self.api_name,
            registry=self.registry,
        )

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

            return await engine.run(self.meta.endpoints)

    async def run(self):
        with get_service() as service:
            self.service = service

            self.bootstrap()
            self.load_metadata()

            return await self.execute()

    def get_api_key(self):
        raise NotImplementedError

    def get_auth_header(self):
        return "Authorization"