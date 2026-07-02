import json
import logging

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert

from src.config.logs.logging_config import *
from src.db.models.config.api import Api, ApiConfig
from src.db.models.config.endpoint_config import Endpoint, EndpointParam

logger = logging.getLogger(__name__)


def flatten_record(record: dict) -> dict:
    """Flatten one level of nested dicts: {'team': {'id': 1}} → {'team_id': 1}.

    '#text' subkeys are normalised to 'name': {'artist': {'#text': 'X'}} → {'artist_name': 'X'}.
    Lists of dicts with an 'id' field: {'artists': [{'id': 'x'}]} → {'artist_id': 'x'}.
    """
    flat: dict = {}
    for k, v in record.items():
        if isinstance(v, dict):
            for nk, nv in v.items():
                sub_key = "name" if nk == "#text" else nk
                flat[f"{k}_{sub_key}"] = nv
        elif isinstance(v, list) and v and isinstance(v[0], dict) and "id" in v[0]:
            singular = k[:-1] if k.endswith("s") else k
            flat[f"{singular}_id"] = v[0]["id"]
        else:
            flat[k] = v
    return flat


class ApiRepository:
    def __init__(self, session):
        self.session = session

    def get_or_create_api(
        self, name: str, description: str | None = None, base_url: str | None = None
    ) -> Api:
        logger.info(f"Fetching or creating API record for name: {name}")
        stmt = select(Api).where(Api.name == name)
        api_record = self.session.execute(stmt).scalars().first()
        if api_record:
            logger.info(f"API record found for name: {name}")
            return api_record
        api_record = Api(name=name, description=description, base_url=base_url)
        self.session.add(api_record)
        self.session.commit()
        logger.info(f"API record created for name: {name}")
        return api_record

    def get_config(self, api_id: int) -> dict[str, str]:
        logger.info("Fetching current API configuration from the database.")
        query = select(ApiConfig.parameter_name, ApiConfig.parameter_value).where(
            ApiConfig.api_id == api_id
        )
        rows = self.session.execute(query).fetchall()
        logger.info(f"Fetched {len(rows)} API config records.")
        return {row.parameter_name: row.parameter_value for row in rows}

    def add_config(
        self,
        api_id: int,
        parameter_name: str,
        parameter_value: str,
        overwrite: bool = True,
    ):
        logger.info(f"Adding API config: {parameter_name}")
        statement = insert(ApiConfig).values(
            api_id=api_id,
            parameter_name=parameter_name,
            parameter_value=parameter_value,
        )
        if overwrite:
            statement = statement.on_conflict_do_update(
                constraint="uq_api_config_api_param",
                set_={"parameter_value": parameter_value},
            )
        else:
            statement = statement.on_conflict_do_nothing(
                constraint="uq_api_config_api_param",
            )
        self.session.execute(statement)
        self.session.commit()

    def upsert_endpoint(
        self,
        api_id: int,
        logical_name: str,
        path_template: str,
        exec_order: int = 999,
        is_active: bool = True,
        db_target: str | None = None,
        db_target_column: str | None = None,
        db_source_field: str | None = None,
        response_path: str | None = None,
    ) -> Endpoint:
        logger.info(f"Upserting endpoint for API {api_id}: {logical_name}")
        stmt = select(Endpoint).where(
            Endpoint.api_id == api_id, Endpoint.logical_name == logical_name
        )
        ep = self.session.execute(stmt).scalars().first()
        if ep:
            ep.path_template = path_template
            ep.exec_order = exec_order
            ep.is_active = is_active
            ep.db_target = db_target
            ep.db_target_column = db_target_column
            ep.db_source_field = db_source_field
            ep.response_path = response_path
            self.session.commit()
            return ep
        ep = Endpoint(
            api_id=api_id,
            logical_name=logical_name,
            path_template=path_template,
            exec_order=exec_order,
            is_active=is_active,
            db_target=db_target,
            db_target_column=db_target_column,
            db_source_field=db_source_field,
            response_path=response_path,
        )
        self.session.add(ep)
        self.session.flush()
        self.session.commit()
        logger.info(f"Endpoint upserted for API {api_id}: {logical_name}")
        return ep

    def upsert_endpoint_param(
        self,
        endpoint_id: int,
        param_name: str,
        required: bool = False,
        default_value: str | None = None,
        value_type: str = "string",
        source_table: str | None = None,
        source_column: str | None = None,
        is_distinct: bool = False,
    ) -> EndpointParam:
        logger.info(f"Upserting param '{param_name}' for endpoint {endpoint_id}")
        stmt = select(EndpointParam).where(
            EndpointParam.endpoint_id == endpoint_id,
            EndpointParam.param_name == param_name,
        )
        param = self.session.execute(stmt).scalars().first()
        if param:
            param.required = required
            param.default_value = default_value
            param.value_type = value_type
            param.source_table = source_table
            param.source_column = source_column
            param.is_distinct = is_distinct
            self.session.commit()
            return param
        param = EndpointParam(
            endpoint_id=endpoint_id,
            param_name=param_name,
            required=required,
            default_value=default_value,
            value_type=value_type,
            source_table=source_table,
            source_column=source_column,
            is_distinct=is_distinct,
        )
        self.session.add(param)
        self.session.flush()
        self.session.commit()
        return param

    def get_ordered_endpoints(self, api_id: int) -> list[dict]:
        logger.info(f"Fetching ordered endpoints for API {api_id}")
        stmt = (
            select(Endpoint)
            .where(Endpoint.api_id == api_id, Endpoint.is_active == True)
            .order_by(Endpoint.exec_order.asc())
        )
        rows = self.session.execute(stmt).scalars().all()
        logger.info(f"Fetched {len(rows)} endpoints for API {api_id}")
        return [
            {
                "id": r.id,
                "logical_name": r.logical_name,
                "path_template": r.path_template,
                "exec_order": r.exec_order,
                "db_target": r.db_target,
                "db_target_column": r.db_target_column,
                "db_source_field": r.db_source_field,
                "response_path": r.response_path,
            }
            for r in rows
        ]

    def get_endpoint_params(self, endpoint_id: int) -> list[dict]:
        logger.info(f"Fetching parameters for endpoint {endpoint_id}")
        stmt = select(EndpointParam).where(EndpointParam.endpoint_id == endpoint_id)
        rows = self.session.execute(stmt).scalars().all()
        logger.info(f"Fetched {len(rows)} parameters for endpoint {endpoint_id}")
        return [
            {
                "param_name": r.param_name,
                "required": r.required,
                "default_value": r.default_value,
                "value_type": r.value_type,
                "source_table": r.source_table,
                "source_column": r.source_column,
                "is_distinct": r.is_distinct,
            }
            for r in rows
        ]

    def save_to_table(
        self,
        schema_table: str,
        db_column: str,
        values: list,
        extra_fields: dict | None = None,
    ):
        """Insert a list of values into a target table, with optional extra columns."""
        schema, table = schema_table.split(".", 1)
        extra = extra_fields or {}
        all_cols = [db_column] + list(extra.keys())
        col_list = ", ".join(f'"{c}"' for c in all_cols)
        param_list = ", ".join(f":{c}" for c in all_cols)
        logger.info(f"Saving {len(values)} records to {schema_table}.{db_column}")
        for value in values:
            params = {db_column: str(value), **extra}
            stmt = text(
                f'INSERT INTO "{schema}"."{table}" ({col_list}) '
                f"VALUES ({param_list}) ON CONFLICT DO NOTHING"
            )
            self.session.execute(stmt, params)
        self.session.commit()

    def save_records(self, schema_table: str, records: list[dict]) -> None:
        """Insert a list of dicts into a target table, skipping unknown fields.

        Fields named 'id' in the source are remapped to 'fighter_id' if that
        column exists on the target table.
        """
        if not records:
            return
        schema, table = schema_table.split(".", 1)
        col_rows = self.session.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = :s AND table_name = :t"
            ),
            {"s": schema, "t": table},
        ).fetchall()
        valid_cols = {r[0] for r in col_rows} - {"id"}
        preferred = f"{table}_id"
        id_remap = preferred if preferred in valid_cols else next(
            (col for col in valid_cols if col.endswith("_id") and col != "api_id"),
            None,
        )

        logger.info(f"Saving {len(records)} records to {schema_table}")
        for record in records:
            if record is None:
                continue
            flat = flatten_record(record)

            row = {}
            for k, v in flat.items():
                key = id_remap if (k == "id" and id_remap) else k
                if key in valid_cols:
                    row[key] = json.dumps(v) if isinstance(v, (dict, list)) else v
            if not row:
                continue
            col_list = ", ".join(f'"{c}"' for c in row)
            param_list = ", ".join(f":{c}" for c in row)
            stmt = text(
                f'INSERT INTO "{schema}"."{table}" ({col_list}) '
                f"VALUES ({param_list}) ON CONFLICT DO NOTHING"
            )
            try:
                self.session.execute(stmt, row)
            except Exception as e:
                self.session.rollback()
                logger.warning(f"Skipped record in {schema_table}: {e}")
        self.session.commit()

    def get_source_values(
        self, schema_table: str, column: str, distinct: bool = False
    ) -> list[str]:
        """Return all values from a column in the given table."""
        schema, table = schema_table.split(".", 1)
        distinct_kw = "DISTINCT " if distinct else ""
        logger.info(f"Loading source values from {schema_table}.{column}")
        rows = self.session.execute(
            text(f'SELECT {distinct_kw}"{column}" FROM "{schema}"."{table}"')
        ).fetchall()
        return [row[0] for row in rows]

    def get_max_value(self, schema_table: str, column: str):
        """Return the max value of a column in the given table, or None if empty."""
        schema, table = schema_table.split(".", 1)
        logger.info(f"Loading max value from {schema_table}.{column}")
        row = self.session.execute(
            text(f'SELECT MAX("{column}") FROM "{schema}"."{table}"')
        ).first()
        return row[0] if row else None
