from src.services.api_service import ApiService


class ApiRegistry:
    def __init__(self, service: ApiService):
        self.service = service

    def get_api(self, name: str):
        return self.service.repository.get_or_create_api(name=name)

    def get_api_id(self, name: str) -> int:
        return self.get_api(name).id

    def get_config(self, api_id: int):
        return self.service.repository.get_config(api_id)

    def update_config(self, api_id: int, parameter_name: str, parameter_value: str):
        self.service.repository.add_config(
            api_id=api_id,
            parameter_name=parameter_name,
            parameter_value=parameter_value,
        )

    def get_endpoints(self, api_id: int):
        return self.service.repository.get_ordered_endpoints(api_id)

    def get_endpoint_params(self, endpoint_id: int) -> list[dict]:
        return self.service.repository.get_endpoint_params(endpoint_id)

    def save_to_table(
        self,
        schema_table: str,
        db_column: str,
        values: list,
        extra_fields: dict | None = None,
    ):
        self.service.repository.save_to_table(
            schema_table, db_column, values, extra_fields=extra_fields
        )

    def save_records(self, schema_table: str, records: list[dict]) -> None:
        self.service.repository.save_records(schema_table, records)

    def upsert_records(
        self,
        schema_table: str,
        records: list[dict],
        conflict_column: str,
        update_columns: list[str],
    ) -> None:
        self.service.repository.upsert_records(
            schema_table, records, conflict_column, update_columns
        )

    def update_movie_ratings(self, schema_table: str, records: list[dict]) -> None:
        self.service.repository.update_movie_ratings(schema_table, records)

    def update_show_ratings(self, schema_table: str, records: list[dict]) -> None:
        self.service.repository.update_show_ratings(schema_table, records)

    def get_source_values(
        self, schema_table: str, column: str, distinct: bool = False
    ) -> list[str]:
        return self.service.repository.get_source_values(
            schema_table, column, distinct=distinct
        )

    def get_max_value(self, schema_table: str, column: str):
        return self.service.repository.get_max_value(schema_table, column)

    def get_incomplete_ids(self, schema_table: str, id_column: str, check_column: str) -> list[str]:
        return self.service.repository.get_incomplete_ids(schema_table, id_column, check_column)

    def has_incomplete_rows(self, schema_table: str, check_column: str) -> bool:
        return self.service.repository.has_incomplete_rows(schema_table, check_column)
