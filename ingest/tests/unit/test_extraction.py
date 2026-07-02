from src.api.execution_engine import _extract_field


def test_extract_field_from_list_of_dicts():
    records = [{"name": "MMA"}, {"name": "Boxing"}, {"name": "Kickboxing"}]
    assert _extract_field(records, "name") == ["MMA", "Boxing", "Kickboxing"]


def test_extract_field_skips_records_missing_the_field():
    records = [{"name": "MMA"}, {"other": "x"}, {"name": "Boxing"}]
    assert _extract_field(records, "name") == ["MMA", "Boxing"]


def test_extract_field_from_plain_string_list():
    # API returns bare strings rather than objects
    records = ["MMA", "Boxing", "Kickboxing"]
    assert _extract_field(records, "anything") == ["MMA", "Boxing", "Kickboxing"]


def test_extract_field_empty_input():
    assert _extract_field([], "name") == []


def test_extract_field_all_records_missing_field():
    records = [{"id": 1}, {"id": 2}]
    assert _extract_field(records, "name") == []
