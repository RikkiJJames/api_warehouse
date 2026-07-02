import pytest
from src.api.execution_engine import ExecutionContext, Resolver


@pytest.fixture
def ctx():
    return ExecutionContext()


@pytest.fixture
def resolver(ctx):
    return Resolver(ctx)


def test_resolve_template_with_no_variables(resolver):
    assert resolver.resolve("categories") == "categories"


def test_resolve_direct_context_variable(ctx, resolver):
    ctx.store("category", "MMA")
    assert resolver.resolve("fighters/{category}") == "fighters/MMA"


def test_resolve_multiple_variables(ctx, resolver):
    ctx.store("league", "UFC")
    ctx.store("year", "2024")
    assert resolver.resolve("{league}/events/{year}") == "UFC/events/2024"


def test_resolve_falls_back_to_searching_datasets(ctx, resolver):
    ctx.store("categories", [{"name": "MMA"}, {"name": "Boxing"}])
    # {name} is not stored directly — engine searches inside the categories list
    assert resolver.resolve("fighters/{name}") == "fighters/MMA"


def test_resolve_direct_takes_priority_over_dataset_search(ctx, resolver):
    ctx.store("name", "direct_value")
    ctx.store("categories", [{"name": "from_dataset"}])
    assert resolver.resolve("{name}") == "direct_value"


def test_resolve_missing_variable_raises(resolver):
    with pytest.raises(ValueError, match="Cannot resolve variable: category"):
        resolver.resolve("fighters/{category}")


def test_resolve_converts_value_to_string(ctx, resolver):
    ctx.store("page", 3)
    assert resolver.resolve("events?page={page}") == "events?page=3"


def test_execution_context_store_and_get(ctx):
    ctx.store("key", [1, 2, 3])
    assert ctx.get("key") == [1, 2, 3]


def test_execution_context_get_missing_returns_none(ctx):
    assert ctx.get("nonexistent") is None


def test_execution_context_find_first_field_returns_first_match(ctx):
    ctx.store("categories", [{"name": "MMA"}, {"name": "Boxing"}])
    assert ctx.find_first_field("name") == "MMA"


def test_execution_context_find_first_field_missing_returns_none(ctx):
    ctx.store("categories", [{"id": 1}])
    assert ctx.find_first_field("name") is None


def test_execution_context_find_first_field_skips_non_lists(ctx):
    ctx.store("scalar", "not a list")
    ctx.store("data", [{"name": "MMA"}])
    assert ctx.find_first_field("name") == "MMA"
