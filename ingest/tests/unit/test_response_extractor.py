from src.api.response_extractor import ResponseExtractor


def test_extract_list_response():
    ext = ResponseExtractor()
    assert ext.extract([{"id": 1}], None) == [{"id": 1}]


def test_extract_single_level_response_path():
    ext = ResponseExtractor()
    raw = {"response": [{"id": 1}, {"id": 2}]}
    assert ext.extract(raw, "response") == [{"id": 1}, {"id": 2}]


def test_extract_dot_notation_response_path():
    ext = ResponseExtractor()
    raw = {"data": {"user_books": [{"id": 1}]}}
    assert ext.extract(raw, "data.user_books") == [{"id": 1}]


def test_extract_dot_notation_missing_intermediate_key():
    ext = ResponseExtractor()
    assert ext.extract({"data": {}}, "data.user_books") == []


def test_extract_dot_notation_non_dict_intermediate():
    ext = ResponseExtractor()
    assert ext.extract({"data": [1, 2, 3]}, "data.user_books") == []


def test_extract_common_convention_keys():
    ext = ResponseExtractor()
    assert ext.extract({"items": [{"id": 1}]}, None) == [{"id": 1}]


def test_extract_no_response_path_non_list_dict():
    ext = ResponseExtractor()
    assert ext.extract({"foo": "bar"}, None) == []
