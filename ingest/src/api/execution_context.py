from typing import Any

class ExecutionContext:
    def __init__(self):
        self.data: dict[str, Any] = {}

    def store(self, key: str, value: Any):
        self.data[key] = value

    def get(self, key: str):
        return self.data.get(key)

    def find_first_field(self, field: str):
        """
        Fallback search across all stored datasets.
        Avoids tight coupling to endpoint names.
        """
        for dataset in self.data.values():
            if isinstance(dataset, list):
                for item in dataset:
                    if isinstance(item, dict) and field in item:
                        return item[field]
        return None