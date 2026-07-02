from src.core.api_registry import ApiRegistry


class ApiClient:
    def __init__(self, registry: ApiRegistry, api_name: str):
        self.registry = registry
        self.api_name = api_name

        self.api = self.registry.get_api(api_name)
        self.api_id = self.api.id

        self.config = self.registry.get_config(self.api_id)
        self.endpoints = self.registry.get_endpoints(self.api_id)
