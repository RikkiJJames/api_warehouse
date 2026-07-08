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
    A single-item list of dicts with no 'id' — e.g. a GraphQL one-to-many
    relation aliased down to its latest row, {'read': [{'started_at': 'x'}]}
    — flattens like a nested dict instead: {'read_started_at': 'x'}.
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
        elif isinstance(v, list) and len(v) == 1 and isinstance(v[0], dict):
            for nk, nv in v[0].items():
                flat[f"{k}_{nk}"] = nv
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
        method: str = "GET",
        query: str | None = None,
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
            ep.method = method
            ep.query = query
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
            method=method,
            query=query,
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
                "method": r.method,
                "query": r.query,
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

    def _column_info(self, schema: str, table: str) -> tuple[set[str], str | None]:
        """Return the target table's column names and its preferred 'id' remap column."""
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
        return valid_cols, id_remap

    def _build_row(self, record: dict, valid_cols: set[str], id_remap: str | None) -> dict:
        """Flatten a record and keep only fields that map to a known column."""
        flat = flatten_record(record)
        row = {}
        for k, v in flat.items():
            key = id_remap if (k == "id" and id_remap) else k
            if key in valid_cols:
                row[key] = json.dumps(v) if isinstance(v, (dict, list)) else v
        return row

    def save_records(self, schema_table: str, records: list[dict]) -> None:
        """Insert a list of dicts into a target table, skipping unknown fields.

        Fields named 'id' in the source are remapped to 'fighter_id' if that
        column exists on the target table.
        """
        if not records:
            return
        schema, table = schema_table.split(".", 1)
        valid_cols, id_remap = self._column_info(schema, table)

        logger.info(f"Saving {len(records)} records to {schema_table}")
        for record in records:
            if record is None:
                continue
            row = self._build_row(record, valid_cols, id_remap)
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

    def upsert_records(
        self,
        schema_table: str,
        records: list[dict],
        conflict_column: str,
        update_columns: list[str],
    ) -> None:
        """Insert records, updating update_columns in place when conflict_column
        already exists — used where a source event's id is stable but fields
        like a watched/rated timestamp can be corrected after the fact.
        """
        if not records:
            return
        schema, table = schema_table.split(".", 1)
        valid_cols, id_remap = self._column_info(schema, table)

        logger.info(f"Upserting {len(records)} records into {schema_table} on {conflict_column}")
        for record in records:
            if record is None:
                continue
            row = self._build_row(record, valid_cols, id_remap)
            if conflict_column not in row:
                continue

            col_list = ", ".join(f'"{c}"' for c in row)
            param_list = ", ".join(f":{c}" for c in row)
            update_set = ", ".join(
                f'"{c}" = EXCLUDED."{c}"' for c in update_columns if c in row
            )
            conflict_clause = (
                f'DO UPDATE SET {update_set}' if update_set else "DO NOTHING"
            )
            stmt = text(
                f'INSERT INTO "{schema}"."{table}" ({col_list}) '
                f'VALUES ({param_list}) '
                f'ON CONFLICT ("{conflict_column}") {conflict_clause}'
            )
            try:
                self.session.execute(stmt, row)
            except Exception as e:
                self.session.rollback()
                logger.warning(f"Skipped record in {schema_table}: {e}")
        self.session.commit()

    def update_movie_ratings(self, schema_table: str, records: list[dict]) -> None:
        """Apply personal ratings from Trakt's sync/ratings/movies onto the
        matching watched_movies rows, keyed by the movie's Trakt id.
        """
        if not records:
            return
        schema, table = schema_table.split(".", 1)
        logger.info(f"Updating {len(records)} movie ratings in {schema_table}")
        stmt = text(
            f'UPDATE "{schema}"."{table}" '
            f'SET my_rating = :rating, my_rated_at = :rated_at '
            f"WHERE (movie_ids->>'trakt')::bigint = :trakt_id"
        )
        for record in records:
            if not isinstance(record, dict):
                continue
            trakt_id = ((record.get("movie") or {}).get("ids") or {}).get("trakt")
            if trakt_id is None:
                continue
            try:
                self.session.execute(
                    stmt,
                    {
                        "rating": record.get("rating"),
                        "rated_at": record.get("rated_at"),
                        "trakt_id": trakt_id,
                    },
                )
            except Exception as e:
                self.session.rollback()
                logger.warning(f"Skipped movie rating update in {schema_table}: {e}")
        self.session.commit()

    def update_show_ratings(self, schema_table: str, records: list[dict]) -> None:
        """Apply personal ratings from Trakt's sync/ratings/shows onto every
        watched_episodes row for the matching show, keyed by the show's Trakt id.
        """
        if not records:
            return
        schema, table = schema_table.split(".", 1)
        logger.info(f"Updating {len(records)} show ratings in {schema_table}")
        stmt = text(
            f'UPDATE "{schema}"."{table}" '
            f'SET show_my_rating = :rating, show_my_rated_at = :rated_at '
            f"WHERE (show_ids->>'trakt')::bigint = :trakt_id"
        )
        for record in records:
            if not isinstance(record, dict):
                continue
            trakt_id = ((record.get("show") or {}).get("ids") or {}).get("trakt")
            if trakt_id is None:
                continue
            try:
                self.session.execute(
                    stmt,
                    {
                        "rating": record.get("rating"),
                        "rated_at": record.get("rated_at"),
                        "trakt_id": trakt_id,
                    },
                )
            except Exception as e:
                self.session.rollback()
                logger.warning(f"Skipped show rating update in {schema_table}: {e}")
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
