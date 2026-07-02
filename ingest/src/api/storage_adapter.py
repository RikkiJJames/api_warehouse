class StorageAdapter:
    def __init__(self, registry, api_id=None):
        self.registry = registry
        self.api_id = api_id

    def save(self, endpoint: dict, logical_name: str, records: list, extra: dict | None = None):
        db_target = endpoint.get("db_target")

        if not db_target:
            return None

        extra = extra or {}
        if self.api_id:
            extra["api_id"] = self.api_id

        db_source_field = endpoint.get("db_source_field")
        db_target_column = endpoint.get("db_target_column")

        if db_source_field and db_target_column:
            values = [
                r.get(db_source_field)
                for r in records
                if isinstance(r, dict) and db_source_field in r
            ]

            self.registry.save_to_table(
                db_target,
                db_target_column,
                values,
                extra_fields=extra or None,
            )
        else:
            enriched = [
                {**r, **extra} if isinstance(r, dict) else r
                for r in records
            ]
            self.registry.save_records(db_target, enriched)