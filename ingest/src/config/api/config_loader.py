import logging
import os
from pathlib import Path

import yaml

from src.config.logs.logging_config import *

from .schemas import ApiSpec

logger = logging.getLogger(__name__)


def _env_var_constructor(loader: yaml.Loader, node: yaml.ScalarNode) -> str:
    var_name = loader.construct_scalar(node)
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(f"Environment variable '{var_name}' is not set.")
    return value


def _env_var_optional_constructor(
    loader: yaml.Loader, node: yaml.ScalarNode
) -> str | None:
    var_name = loader.construct_scalar(node)
    return os.getenv(var_name)


yaml.add_constructor("!env", _env_var_constructor, Loader=yaml.SafeLoader)
yaml.add_constructor(
    "!env_optional", _env_var_optional_constructor, Loader=yaml.SafeLoader
)


class ConfigLoader:
    def __init__(self, config_dir: str = "mma"):
        self.config_dir = self.resolve_config_path(config_dir)

    def resolve_config_path(self, config_dir: str) -> Path:
        config_path = (
            Path(config_dir)
            if Path(config_dir).is_absolute()
            else Path(__file__).parent / config_dir
        )
        if not config_path.exists():
            logger.error(f"Configuration directory does not exist: {config_path}.")
            raise FileNotFoundError(
                f"Configuration directory does not exist: {config_path}."
            )
        return config_path

    def load_all(self) -> list[ApiSpec]:
        logger.info(
            f"Loading all configuration files from directory: {self.config_dir}"
        )
        configs = []

        for file in self.config_dir.iterdir():
            if file.suffix in {".yaml", ".yml"}:
                with open(file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)

                    logger.info(f"Loaded configuration from: {file}")
                    configs.append(ApiSpec.model_validate(data))

        return configs
