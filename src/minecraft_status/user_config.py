from __future__ import annotations

from typing import Any

from . import config as defaults
from .secure_store import load_config, save_config


def load_user_config() -> dict[str, Any]:
    data = dict(defaults.DEFAULT_USER_CONFIG)
    data.update(load_config())
    return data


def save_user_config(data: dict[str, Any]) -> None:
    merged = dict(defaults.DEFAULT_USER_CONFIG)
    merged.update(data)
    save_config(merged)


def get_client_id() -> str | None:
    value = load_user_config().get("client_id")
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def set_client_id(client_id: str) -> None:
    value = client_id.strip()
    if not value:
        raise ValueError("Client ID cannot be empty.")
    data = load_user_config()
    data["client_id"] = value
    save_user_config(data)


def validate_client_id_format(client_id: str) -> bool:
    value = client_id.strip()
    return value.isdigit() and 17 <= len(value) <= 21


def get_setting(name: str, fallback: Any = None) -> Any:
    return load_user_config().get(name, fallback)


def set_setting(name: str, value: Any) -> None:
    data = load_user_config()
    data[name] = value
    save_user_config(data)
