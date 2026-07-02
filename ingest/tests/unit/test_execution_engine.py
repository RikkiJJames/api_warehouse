import pytest
from unittest.mock import MagicMock, AsyncMock
from src.api.execution_engine import ExecutionEngine


def make_endpoint(
    id=1,
    logical_name="categories",
    path_template="categories",
    exec_order=1,
    db_target=None,
    db_target_column=None,
    db_source_field=None,
):
    return {
        "id": id,
        "logical_name": logical_name,
        "path_template": path_template,
        "exec_order": exec_order,
        "db_target": db_target,
        "db_target_column": db_target_column,
        "db_source_field": db_source_field,
    }


def make_param(
    param_name, source_table=None, source_column=None, required=False, is_distinct=False
):
    return {
        "param_name": param_name,
        "required": required,
        "default_value": None,
        "value_type": "string",
        "source_table": source_table,
        "source_column": source_column,
        "is_distinct": is_distinct,
    }


def _make_api_mock(responses: dict):
    """Return an async get_endpoint mock that understands query params.

    Response dict keys can be either plain paths ("categories") or
    path+query strings ("fighters?category=MMA") for parameterised calls.
    """
    api = MagicMock()

    async def get_endpoint(path, params=None, **kw):
        if params:
            qs = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
            key = f"{path}?{qs}"
            if key in responses:
                return responses[key]
        return responses.get(path, [])

    api.get_endpoint = get_endpoint
    api.throttle = AsyncMock()
    return api


def make_engine(responses: dict, params=None, source_values=None, api_id=None):
    """Build an ExecutionEngine with a fake HTTP client and registry."""
    api = _make_api_mock(responses)

    registry = MagicMock()
    registry.get_endpoint_params.return_value = params or []
    registry.get_source_values.return_value = source_values or []

    return ExecutionEngine(api, registry, api_id=api_id), registry


# ── single endpoint ────────────────────────────────────────────────────────────


async def test_single_endpoint_returns_ok_status():
    engine, _ = make_engine({"categories": [{"name": "MMA"}, {"name": "Boxing"}]})
    results = await engine.run([make_endpoint()])
    assert results["categories"]["status"] == "ok"
    assert results["categories"]["count"] == 2


async def test_result_stored_in_context_when_no_db_target():
    engine, _ = make_engine({"categories": [{"name": "MMA"}]})
    await engine.run([make_endpoint()])
    assert engine.context.get("categories") == [{"name": "MMA"}]


async def test_result_saved_to_db_when_db_target_configured():
    engine, registry = make_engine(
        {"categories": [{"name": "MMA"}, {"name": "Boxing"}]},
        api_id=1,
    )
    ep = make_endpoint(
        db_target="mma.categories",
        db_target_column="category_name",
        db_source_field="name",
    )
    await engine.run([ep])
    registry.save_to_table.assert_called_once_with(
        "mma.categories",
        "category_name",
        ["MMA", "Boxing"],
        extra_fields={"api_id": 1},
    )


async def test_db_target_result_not_stored_in_context():
    engine, _ = make_engine({"categories": [{"name": "MMA"}]})
    ep = make_endpoint(
        db_target="mma.categories",
        db_target_column="category_name",
        db_source_field="name",
    )
    await engine.run([ep])
    assert engine.context.get("categories") is None


# ── iterated endpoint ──────────────────────────────────────────────────────────


async def test_iterated_endpoint_runs_once_per_source_value():
    responses = {
        "fighters?category=Boxing": [{"name": "Floyd Mayweather"}],
        "fighters?category=MMA": [{"name": "Jon Jones"}],
    }
    params = [
        make_param(
            "category", source_table="mma.categories", source_column="category_name"
        )
    ]
    engine, _ = make_engine(responses, params=params, source_values=["MMA", "Boxing"])

    ep = make_endpoint(
        id=2, logical_name="fighters", path_template="fighters", exec_order=2
    )
    results = await engine.run([ep])

    assert results["fighters"]["status"] == "ok"
    assert results["fighters"]["count"] == 2


async def test_iterated_endpoint_total_count_is_cumulative():
    responses = {
        "fighters?category=Boxing": [{"name": "c"}],
        "fighters?category=MMA": [{"name": "a"}, {"name": "b"}],
    }
    params = [
        make_param(
            "category", source_table="mma.categories", source_column="category_name"
        )
    ]
    engine, _ = make_engine(responses, params=params, source_values=["MMA", "Boxing"])

    ep = make_endpoint(
        id=2, logical_name="fighters", path_template="fighters", exec_order=2
    )
    results = await engine.run([ep])
    assert results["fighters"]["count"] == 3


async def test_iterated_endpoint_partial_failure_continues():
    responses = {
        "fighters?category=MMA": [{"name": "Jon Jones"}],
    }
    api = MagicMock()

    async def get_endpoint(path, params=None, **kw):
        if params and params.get("category") == "Boxing":
            raise RuntimeError("timeout")
        if params:
            qs = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
            return responses.get(f"{path}?{qs}", [])
        return responses.get(path, [])

    api.get_endpoint = get_endpoint
    api.throttle = AsyncMock()

    registry = MagicMock()
    registry.get_endpoint_params.return_value = [
        make_param(
            "category", source_table="mma.categories", source_column="category_name"
        )
    ]
    registry.get_source_values.return_value = ["MMA", "Boxing"]

    engine = ExecutionEngine(api, registry)
    ep = make_endpoint(
        id=2, logical_name="fighters", path_template="fighters", exec_order=2
    )
    results = await engine.run([ep])

    # One success, one failure — should not raise, count should be 1
    assert results["fighters"]["count"] == 1


# ── error handling ─────────────────────────────────────────────────────────────


async def test_failed_endpoint_returns_error_status():
    api = MagicMock()
    api.get_endpoint = AsyncMock(side_effect=RuntimeError("API error"))
    registry = MagicMock()
    registry.get_endpoint_params.return_value = []

    engine = ExecutionEngine(api, registry)
    results = await engine.run([make_endpoint()])
    assert results["categories"]["status"] == "error"
    assert "API error" in results["categories"]["error"]


async def test_failed_endpoint_does_not_stop_subsequent_endpoints():
    api = MagicMock()

    async def get_endpoint(path, **kw):
        if path == "categories":
            raise RuntimeError("timeout")
        return [{"id": 1}]

    api.get_endpoint = get_endpoint
    registry = MagicMock()
    registry.get_endpoint_params.return_value = []

    engine = ExecutionEngine(api, registry)
    endpoints = [
        make_endpoint(
            id=1, logical_name="categories", path_template="categories", exec_order=1
        ),
        make_endpoint(
            id=2, logical_name="events", path_template="events", exec_order=2
        ),
    ]
    results = await engine.run(endpoints)

    assert results["categories"]["status"] == "error"
    assert results["events"]["status"] == "ok"


# ── ordering ───────────────────────────────────────────────────────────────────


# ── api_id injection ───────────────────────────────────────────────────────────


async def test_api_id_included_in_save_to_table_extra_fields():
    engine, registry = make_engine(
        {"categories": [{"name": "MMA"}, {"name": "Boxing"}]},
        api_id=1,
    )
    ep = make_endpoint(
        db_target="mma.categories",
        db_target_column="category_name",
        db_source_field="name",
    )
    await engine.run([ep])
    registry.save_to_table.assert_called_once_with(
        "mma.categories",
        "category_name",
        ["MMA", "Boxing"],
        extra_fields={"api_id": 1},
    )


async def test_api_id_absent_when_not_set():
    engine, registry = make_engine(
        {"categories": [{"name": "MMA"}]},
        api_id=None,
    )
    ep = make_endpoint(
        db_target="mma.categories",
        db_target_column="category_name",
        db_source_field="name",
    )
    await engine.run([ep])
    registry.save_to_table.assert_called_once_with(
        "mma.categories",
        "category_name",
        ["MMA"],
        extra_fields=None,
    )


async def test_api_id_merged_into_multi_col_records():
    engine, registry = make_engine(
        {"fighters": [{"id": 691, "name": "Conor McGregor"}]},
        api_id=1,
    )
    ep = make_endpoint(
        logical_name="fighters",
        path_template="fighters",
        db_target="mma.fighters",
    )
    await engine.run([ep])
    saved = registry.save_records.call_args[0][1]
    assert saved[0]["api_id"] == 1


async def test_param_value_merged_into_iterated_records():
    responses = {"fighters?category=MMA": [{"id": 691, "name": "Conor McGregor"}]}
    params = [
        make_param(
            "category", source_table="mma.categories", source_column="category_name"
        )
    ]
    engine, registry = make_engine(
        responses, params=params, source_values=["MMA"], api_id=1
    )
    ep = make_endpoint(
        id=2,
        logical_name="fighters",
        path_template="fighters",
        exec_order=2,
        db_target="mma.fighters",
    )
    await engine.run([ep])
    saved = registry.save_records.call_args[0][1]
    assert saved[0]["category"] == "MMA"
    assert saved[0]["api_id"] == 1


# ── is_distinct ────────────────────────────────────────────────────────────────


async def test_is_distinct_passed_to_get_source_values():
    responses = {"fighters?id=691": []}
    params = [
        make_param(
            "id",
            source_table="mma.fighters",
            source_column="fighter_id",
            is_distinct=True,
        )
    ]
    engine, registry = make_engine(responses, params=params, source_values=[691])
    ep = make_endpoint(
        id=3,
        logical_name="fighter_records",
        path_template="fighters/records",
        exec_order=3,
    )
    await engine.run([ep])
    registry.get_source_values.assert_called_once_with(
        "mma.fighters", "fighter_id", distinct=True
    )


async def test_is_distinct_false_by_default():
    responses = {"fighters?category=MMA": []}
    params = [
        make_param(
            "category", source_table="mma.categories", source_column="category_name"
        )
    ]
    engine, registry = make_engine(responses, params=params, source_values=["MMA"])
    ep = make_endpoint(
        id=2, logical_name="fighters", path_template="fighters", exec_order=2
    )
    await engine.run([ep])
    registry.get_source_values.assert_called_once_with(
        "mma.categories", "category_name", distinct=False
    )


# ── ordering ───────────────────────────────────────────────────────────────────


async def test_endpoints_executed_in_exec_order():
    call_order = []
    api = MagicMock()

    async def get_endpoint(path, **kw):
        call_order.append(path)
        return []

    api.get_endpoint = get_endpoint
    registry = MagicMock()
    registry.get_endpoint_params.return_value = []

    engine = ExecutionEngine(api, registry)
    endpoints = [
        make_endpoint(id=2, logical_name="b", path_template="b", exec_order=2),
        make_endpoint(id=1, logical_name="a", path_template="a", exec_order=1),
    ]
    await engine.run(endpoints)
    assert call_order == ["a", "b"]
