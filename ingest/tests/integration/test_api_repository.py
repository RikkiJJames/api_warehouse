import pytest
from src.db.repositories.api_repository import ApiRepository

pytestmark = pytest.mark.integration


@pytest.fixture
def repo(db_session):
    return ApiRepository(db_session)


# ── Api ────────────────────────────────────────────────────────────────────────


def test_get_or_create_api_creates_new_record(repo):
    api = repo.get_or_create_api(name="mma", base_url="https://example.com")
    assert api.id is not None
    assert api.name == "mma"


def test_get_or_create_api_returns_existing_record(repo):
    first = repo.get_or_create_api(name="mma", base_url="https://example.com")
    second = repo.get_or_create_api(name="mma", base_url="https://example.com")
    assert first.id == second.id


# ── ApiConfig ──────────────────────────────────────────────────────────────────


def test_add_config_stores_key_value(repo):
    api = repo.get_or_create_api(name="mma", base_url="https://example.com")
    repo.add_config(api.id, "api_key", "secret123")
    config = repo.get_config(api.id)
    assert config["api_key"] == "secret123"


def test_add_config_upserts_on_duplicate_param_name(repo):
    api = repo.get_or_create_api(name="mma", base_url="https://example.com")
    repo.add_config(api.id, "api_key", "old_value")
    repo.add_config(api.id, "api_key", "new_value")
    config = repo.get_config(api.id)
    assert config["api_key"] == "new_value"


def test_two_apis_can_share_param_name(repo):
    api1 = repo.get_or_create_api(name="mma", base_url="https://mma.com")
    api2 = repo.get_or_create_api(name="boxing", base_url="https://boxing.com")
    repo.add_config(api1.id, "api_key", "key1")
    repo.add_config(api2.id, "api_key", "key2")
    assert repo.get_config(api1.id)["api_key"] == "key1"
    assert repo.get_config(api2.id)["api_key"] == "key2"


# ── Endpoint ───────────────────────────────────────────────────────────────────


def test_upsert_endpoint_creates_new(repo):
    api = repo.get_or_create_api(name="mma", base_url="https://example.com")
    ep = repo.upsert_endpoint(api.id, "categories", "categories", exec_order=1)
    assert ep.id is not None
    assert ep.logical_name == "categories"


def test_upsert_endpoint_updates_existing(repo):
    api = repo.get_or_create_api(name="mma", base_url="https://example.com")
    repo.upsert_endpoint(api.id, "categories", "categories", exec_order=1)
    updated = repo.upsert_endpoint(api.id, "categories", "categories/v2", exec_order=5)
    assert updated.path_template == "categories/v2"
    assert updated.exec_order == 5


def test_upsert_endpoint_stores_db_target_fields(repo):
    api = repo.get_or_create_api(name="mma", base_url="https://example.com")
    ep = repo.upsert_endpoint(
        api.id,
        "categories",
        "categories",
        db_target="mma.categories",
        db_target_column="category_name",
        db_source_field="name",
    )
    assert ep.db_target == "mma.categories"
    assert ep.db_target_column == "category_name"
    assert ep.db_source_field == "name"


def test_two_apis_can_share_logical_name(repo):
    api1 = repo.get_or_create_api(name="mma", base_url="https://mma.com")
    api2 = repo.get_or_create_api(name="boxing", base_url="https://boxing.com")
    ep1 = repo.upsert_endpoint(api1.id, "categories", "mma/categories")
    ep2 = repo.upsert_endpoint(api2.id, "categories", "boxing/categories")
    assert ep1.id != ep2.id


def test_get_ordered_endpoints_returns_active_only(repo):
    api = repo.get_or_create_api(name="mma", base_url="https://example.com")
    repo.upsert_endpoint(
        api.id, "categories", "categories", exec_order=1, is_active=True
    )
    repo.upsert_endpoint(api.id, "archived", "archived", exec_order=2, is_active=False)
    endpoints = repo.get_ordered_endpoints(api.id)
    names = [e["logical_name"] for e in endpoints]
    assert "categories" in names
    assert "archived" not in names


def test_get_ordered_endpoints_sorted_by_exec_order(repo):
    api = repo.get_or_create_api(name="mma", base_url="https://example.com")
    repo.upsert_endpoint(api.id, "fighters", "fighters", exec_order=2)
    repo.upsert_endpoint(api.id, "categories", "categories", exec_order=1)
    endpoints = repo.get_ordered_endpoints(api.id)
    orders = [e["exec_order"] for e in endpoints]
    assert orders == sorted(orders)


def test_get_ordered_endpoints_includes_db_target_fields(repo):
    api = repo.get_or_create_api(name="mma", base_url="https://example.com")
    repo.upsert_endpoint(
        api.id,
        "categories",
        "categories",
        db_target="mma.categories",
        db_target_column="category_name",
    )
    endpoints = repo.get_ordered_endpoints(api.id)
    assert endpoints[0]["db_target"] == "mma.categories"


# ── EndpointParam ──────────────────────────────────────────────────────────────


def test_upsert_endpoint_param_creates_new(repo):
    api = repo.get_or_create_api(name="mma", base_url="https://example.com")
    ep = repo.upsert_endpoint(api.id, "fighters", "fighters/{category}")
    param = repo.upsert_endpoint_param(
        ep.id,
        "category",
        source_table="mma.categories",
        source_column="category_name",
    )
    assert param.id is not None
    assert param.source_table == "mma.categories"


def test_upsert_endpoint_param_updates_existing(repo):
    api = repo.get_or_create_api(name="mma", base_url="https://example.com")
    ep = repo.upsert_endpoint(api.id, "fighters", "fighters/{category}")
    repo.upsert_endpoint_param(
        ep.id, "category", source_table="mma.categories", source_column="old_col"
    )
    updated = repo.upsert_endpoint_param(
        ep.id, "category", source_table="mma.categories", source_column="category_name"
    )
    assert updated.source_column == "category_name"


def test_get_endpoint_params_returns_source_fields(repo):
    api = repo.get_or_create_api(name="mma", base_url="https://example.com")
    ep = repo.upsert_endpoint(api.id, "fighters", "fighters/{category}")
    repo.upsert_endpoint_param(
        ep.id,
        "category",
        required=True,
        source_table="mma.categories",
        source_column="category_name",
    )
    params = repo.get_endpoint_params(ep.id)
    assert len(params) == 1
    assert params[0]["source_table"] == "mma.categories"
    assert params[0]["source_column"] == "category_name"


# ── save_to_table / get_source_values ─────────────────────────────────────────


def test_save_to_table_inserts_values(repo):
    repo.save_to_table(
        "mma.categories", "category_name", ["MMA", "Boxing", "Kickboxing"]
    )
    values = repo.get_source_values("mma.categories", "category_name")
    assert set(values) == {"MMA", "Boxing", "Kickboxing"}


def test_save_to_table_on_conflict_does_nothing(repo):
    repo.save_to_table("mma.categories", "category_name", ["MMA"])
    repo.save_to_table("mma.categories", "category_name", ["MMA", "Boxing"])
    values = repo.get_source_values("mma.categories", "category_name")
    assert values.count("MMA") == 1


def test_get_source_values_returns_empty_for_empty_table(repo):
    assert repo.get_source_values("mma.categories", "category_name") == []


def test_save_to_table_with_extra_fields(repo):
    api = repo.get_or_create_api(name="mma", base_url="https://mma.com")
    repo.save_to_table(
        "mma.categories",
        "category_name",
        ["MMA", "Boxing"],
        extra_fields={"api_id": api.id},
    )
    from sqlalchemy import text

    rows = repo.session.execute(
        text("SELECT category_name, api_id FROM mma.categories")
    ).fetchall()
    assert all(r.api_id == api.id for r in rows)
    assert {r.category_name for r in rows} == {"MMA", "Boxing"}


def test_get_source_values_distinct_removes_duplicates(repo):
    api = repo.get_or_create_api(name="mma", base_url="https://mma.com")
    # Insert the same fighter_id under two categories
    repo.save_records(
        "mma.fighters",
        [
            {
                "api_id": api.id,
                "fighter_id": 691,
                "name": "Conor McGregor",
                "category": "Lightweight",
            },
            {
                "api_id": api.id,
                "fighter_id": 691,
                "name": "Conor McGregor",
                "category": "Featherweight",
            },
        ],
    )
    all_values = repo.get_source_values("mma.fighters", "fighter_id")
    distinct_values = repo.get_source_values(
        "mma.fighters", "fighter_id", distinct=True
    )
    assert all_values.count(691) == 2
    assert distinct_values.count(691) == 1


# ── save_records ───────────────────────────────────────────────────────────────


def test_save_records_flattens_nested_dicts(repo):
    api = repo.get_or_create_api(name="mma", base_url="https://mma.com")
    record = {
        "api_id": api.id,
        "fighter": {"id": 691, "name": "Conor McGregor", "photo": "https://img.png"},
        "total": {"win": 22, "loss": 6, "draw": 0},
        "ko": {"win": 19, "loss": 2},
        "sub": {"win": 1, "loss": 4},
    }
    repo.save_records("mma.fighter_records", [record])
    from sqlalchemy import text

    row = repo.session.execute(text("SELECT * FROM mma.fighter_records")).fetchone()
    assert row.fighter_id == 691
    assert row.fighter_name == "Conor McGregor"
    assert row.total_win == 22
    assert row.ko_loss == 2
    assert row.sub_win == 1
    assert row.api_id == api.id


def test_save_records_on_conflict_does_nothing(repo):
    api = repo.get_or_create_api(name="mma", base_url="https://mma.com")
    record = {
        "api_id": api.id,
        "fighter": {"id": 691, "name": "Conor McGregor", "photo": ""},
        "total": {"win": 22, "loss": 6, "draw": 0},
        "ko": {"win": 19, "loss": 2},
        "sub": {"win": 1, "loss": 4},
    }
    repo.save_records("mma.fighter_records", [record])
    repo.save_records("mma.fighter_records", [record])
    from sqlalchemy import text

    count = repo.session.execute(
        text("SELECT COUNT(*) FROM mma.fighter_records")
    ).scalar()
    assert count == 1


def test_save_records_skips_unknown_fields(repo):
    api = repo.get_or_create_api(name="mma", base_url="https://mma.com")
    record = {
        "api_id": api.id,
        "fighter": {"id": 692, "name": "Khabib Nurmagomedov", "photo": ""},
        "total": {"win": 29, "loss": 0, "draw": 0},
        "ko": {"win": 8, "loss": 0},
        "sub": {"win": 11, "loss": 0},
        "unknown_field": "should be ignored",
        "nested_unknown": {"also": "ignored"},
    }
    repo.save_records("mma.fighter_records", [record])
    from sqlalchemy import text

    row = repo.session.execute(
        text("SELECT fighter_name FROM mma.fighter_records WHERE fighter_id = 692")
    ).fetchone()
    assert row is not None
    assert row.fighter_name == "Khabib Nurmagomedov"


# ── is_distinct on endpoint params ─────────────────────────────────────────────


def test_upsert_endpoint_param_stores_is_distinct(repo):
    api = repo.get_or_create_api(name="mma", base_url="https://mma.com")
    ep = repo.upsert_endpoint(api.id, "fighter_records", "fighters/records")
    param = repo.upsert_endpoint_param(
        ep.id,
        "id",
        source_table="mma.fighters",
        source_column="fighter_id",
        is_distinct=True,
    )
    assert param.is_distinct is True


def test_get_endpoint_params_returns_is_distinct(repo):
    api = repo.get_or_create_api(name="mma", base_url="https://mma.com")
    ep = repo.upsert_endpoint(api.id, "fighter_records", "fighters/records")
    repo.upsert_endpoint_param(
        ep.id,
        "id",
        source_table="mma.fighters",
        source_column="fighter_id",
        is_distinct=True,
    )
    params = repo.get_endpoint_params(ep.id)
    assert params[0]["is_distinct"] is True
