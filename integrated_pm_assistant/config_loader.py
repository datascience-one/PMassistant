import yaml
from typing import Any, Dict


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def get_data_backend_config(path: str = "config.yaml") -> Dict[str, Any]:
    config = load_config(path)
    return config["data_backend"]


def get_data_backend(path: str = "config.yaml"):
    from data_backend.registry import get_backend
    return get_backend(get_data_backend_config(path))
