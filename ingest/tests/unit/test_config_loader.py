import pytest
import yaml
from src.config.api.config_loader import ConfigLoader


@pytest.fixture
def api_spec():
    return {
        "name": "test_api",
        "description": "Test API",
        "base_url": "https://example.com",
        "api_config": [{"parameter_name": "api_key", "parameter_value": "secret123"}],
        "endpoints": [
            {
                "logical_name": "categories",
                "path_template": "categories",
                "exec_order": 1,
                "is_active": True,
                "db_target": "mma.categories",
                "db_target_column": "category_name",
                "db_source_field": "name",
                "params": [],
            }
        ],
    }


@pytest.fixture
def config_dir(tmp_path, api_spec):
    (tmp_path / "mma.yaml").write_text(yaml.dump(api_spec))
    return tmp_path


def test_loads_single_yaml_file(config_dir):
    loader = ConfigLoader(config_dir=str(config_dir))
    specs = loader.load_all()
    assert len(specs) == 1


def test_parses_api_name_and_url(config_dir):
    loader = ConfigLoader(config_dir=str(config_dir))
    spec = loader.load_all()[0]
    assert spec.name == "test_api"
    assert spec.base_url == "https://example.com"


def test_parses_api_config(config_dir):
    loader = ConfigLoader(config_dir=str(config_dir))
    spec = loader.load_all()[0]
    assert spec.api_config[0].parameter_name == "api_key"
    assert spec.api_config[0].parameter_value == "secret123"


def test_parses_endpoint_fields(config_dir):
    loader = ConfigLoader(config_dir=str(config_dir))
    ep = loader.load_all()[0].endpoints[0]
    assert ep.logical_name == "categories"
    assert ep.exec_order == 1
    assert ep.db_target == "mma.categories"
    assert ep.db_target_column == "category_name"
    assert ep.db_source_field == "name"


def test_skips_non_yaml_files(tmp_path, api_spec):
    (tmp_path / "notes.txt").write_text("ignore me")
    (tmp_path / "spec.yaml").write_text(yaml.dump(api_spec))
    loader = ConfigLoader(config_dir=str(tmp_path))
    assert len(loader.load_all()) == 1


def test_loads_multiple_yaml_files(tmp_path, api_spec):
    spec2 = {**api_spec, "name": "other_api", "base_url": "https://other.com"}
    (tmp_path / "mma.yaml").write_text(yaml.dump(api_spec))
    (tmp_path / "other.yaml").write_text(yaml.dump(spec2))
    loader = ConfigLoader(config_dir=str(tmp_path))
    names = {s.name for s in loader.load_all()}
    assert names == {"test_api", "other_api"}


def test_missing_directory_raises_file_not_found():
    with pytest.raises(FileNotFoundError):
        ConfigLoader(config_dir="/nonexistent/path/xyz")


def test_is_distinct_defaults_to_false(config_dir):
    loader = ConfigLoader(config_dir=str(config_dir))
    ep = loader.load_all()[0].endpoints[0]
    assert ep.params == [] or all(not p.is_distinct for p in ep.params)


def test_is_distinct_parsed_from_yaml(tmp_path):
    spec = {
        "name": "api",
        "description": "d",
        "base_url": "http://x.com",
        "api_config": [],
        "endpoints": [
            {
                "logical_name": "fighter_records",
                "path_template": "fighters/records",
                "exec_order": 3,
                "is_active": True,
                "params": [
                    {
                        "param_name": "id",
                        "required": True,
                        "source_table": "mma.fighters",
                        "source_column": "fighter_id",
                        "is_distinct": True,
                    }
                ],
            }
        ],
    }
    (tmp_path / "spec.yaml").write_text(__import__("yaml").dump(spec))
    loader = ConfigLoader(config_dir=str(tmp_path))
    param = loader.load_all()[0].endpoints[0].params[0]
    assert param.is_distinct is True


def test_endpoint_with_params(tmp_path):
    spec = {
        "name": "api",
        "description": "d",
        "base_url": "http://x.com",
        "api_config": [],
        "endpoints": [
            {
                "logical_name": "fighters",
                "path_template": "fighters/{category}",
                "exec_order": 2,
                "is_active": True,
                "params": [
                    {
                        "param_name": "category",
                        "required": True,
                        "source_table": "mma.categories",
                        "source_column": "category_name",
                    }
                ],
            }
        ],
    }
    (tmp_path / "spec.yaml").write_text(yaml.dump(spec))
    loader = ConfigLoader(config_dir=str(tmp_path))
    ep = loader.load_all()[0].endpoints[0]
    assert ep.params[0].param_name == "category"
    assert ep.params[0].source_table == "mma.categories"
    assert ep.params[0].source_column == "category_name"
