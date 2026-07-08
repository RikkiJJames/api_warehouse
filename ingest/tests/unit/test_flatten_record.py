from src.db.repositories.api_repository import flatten_record


def test_flat_record_unchanged():
    record = {"name": "Jon Jones", "age": 36}
    assert flatten_record(record) == {"name": "Jon Jones", "age": 36}


def test_nested_dict_is_flattened():
    record = {"team": {"id": 40, "name": "SBG Ireland"}}
    assert flatten_record(record) == {"team_id": 40, "team_name": "SBG Ireland"}


def test_mixed_flat_and_nested():
    record = {
        "id": 691,
        "name": "Conor McGregor",
        "team": {"id": 40, "name": "SBG Ireland"},
    }
    result = flatten_record(record)
    assert result["id"] == 691
    assert result["name"] == "Conor McGregor"
    assert result["team_id"] == 40
    assert result["team_name"] == "SBG Ireland"
    assert "team" not in result


def test_fighter_records_response_shape():
    record = {
        "fighter": {"id": 691, "name": "Conor McGregor", "photo": "https://img.png"},
        "total": {"win": 22, "loss": 6, "draw": 0},
        "ko": {"win": 19, "loss": 2},
        "sub": {"win": 1, "loss": 4},
    }
    result = flatten_record(record)
    assert result == {
        "fighter_id": 691,
        "fighter_name": "Conor McGregor",
        "fighter_photo": "https://img.png",
        "total_win": 22,
        "total_loss": 6,
        "total_draw": 0,
        "ko_win": 19,
        "ko_loss": 2,
        "sub_win": 1,
        "sub_loss": 4,
    }


def test_empty_record():
    assert flatten_record({}) == {}


def test_nested_dict_with_empty_value():
    record = {"stats": {}}
    assert flatten_record(record) == {}


def test_non_dict_values_preserved():
    record = {"tags": ["mma", "ufc"], "score": 9.5, "active": True}
    result = flatten_record(record)
    assert result["tags"] == ["mma", "ufc"]
    assert result["score"] == 9.5
    assert result["active"] is True


def test_single_item_list_without_id_is_flattened():
    record = {
        "user_book_id": 1,
        "read": [{"started_at": "2024-01-01", "finished_at": "2024-01-10"}],
    }
    assert flatten_record(record) == {
        "user_book_id": 1,
        "read_started_at": "2024-01-01",
        "read_finished_at": "2024-01-10",
    }


def test_single_item_list_with_id_still_uses_id_remap():
    record = {"artists": [{"id": "x", "name": "ignored"}]}
    assert flatten_record(record) == {"artist_id": "x"}


def test_multi_item_list_without_id_left_as_raw_list():
    record = {"reads": [{"started_at": "a"}, {"started_at": "b"}]}
    assert flatten_record(record) == {"reads": [{"started_at": "a"}, {"started_at": "b"}]}


def test_empty_list_left_as_raw_list():
    record = {"reads": []}
    assert flatten_record(record) == {"reads": []}
