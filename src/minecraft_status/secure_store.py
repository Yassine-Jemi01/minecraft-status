from __future__ import annotations

import base64
import json
import os
import platform
import secrets
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

SERVICE_NAME = "minecraft-status"
KEY_NAME = "local-encryption-key"


def get_config_dir() -> Path:
    override = os.environ.get("MINECRAFT_STATUS_CONFIG_DIR")
    if override:
        return Path(override).expanduser()

    system = platform.system()

    if system == "Windows":
        base = os.environ.get("APPDATA")
        return (Path(base) if base else Path.home() / "AppData/Roaming") / SERVICE_NAME

    if system == "Darwin":
        return Path.home() / "Library/Application Support" / SERVICE_NAME

    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / SERVICE_NAME


def get_encrypted_config_path() -> Path:
    return get_config_dir() / "config.enc"


def get_legacy_plaintext_config_path() -> Path:
    return get_config_dir() / "config.json"


def get_fallback_key_path() -> Path:
    return get_config_dir() / "secret.key"


def _key_from_keyring() -> bytes | None:
    try:
        import keyring  # type: ignore
    except ImportError:
        return None

    try:
        encoded = keyring.get_password(
            SERVICE_NAME,
            KEY_NAME,
        )
    except Exception:
        return None

    if encoded:
        try:
            return encoded.encode("ascii")
        except UnicodeEncodeError:
            return None

    key = Fernet.generate_key()

    try:
        keyring.set_password(
            SERVICE_NAME,
            KEY_NAME,
            key.decode("ascii"),
        )
    except Exception:
        return None

    return key


def _key_from_file() -> bytes:
    path = get_fallback_key_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        return path.read_bytes().strip()

    key = Fernet.generate_key()
    path.write_bytes(key)

    try:
        os.chmod(path, 0o600)
    except OSError:
        pass

    return key


def _get_key() -> bytes:
    key = _key_from_keyring()
    if key is not None:
        return key
    return _key_from_file()


def _encrypt(payload: dict[str, Any]) -> bytes:
    key = _get_key()
    token = Fernet(key).encrypt(
        json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    return token


def _decrypt(token: bytes) -> dict[str, Any]:
    key = _get_key()

    try:
        raw = Fernet(key).decrypt(token)
    except InvalidToken as exc:
        raise RuntimeError(
            "The encrypted user configuration cannot be decrypted. "
            "The local encryption key may be missing or invalid."
        ) from exc

    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            "The encrypted user configuration is corrupted."
        ) from exc

    if not isinstance(data, dict):
        raise RuntimeError(
            "The encrypted user configuration has an invalid format."
        )

    return data


def load_config() -> dict[str, Any]:
    encrypted = get_encrypted_config_path()

    if encrypted.exists():
        return _decrypt(encrypted.read_bytes())

    legacy = get_legacy_plaintext_config_path()
    if legacy.exists():
        try:
            data = json.loads(legacy.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(
                "The old user configuration could not be read."
            ) from exc

        if not isinstance(data, dict):
            raise RuntimeError(
                "The old user configuration has an invalid format."
            )

        save_config(data)
        try:
            legacy.unlink()
        except OSError:
            pass
        return data

    return {}


def save_config(data: dict[str, Any]) -> None:
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)

    encrypted = get_encrypted_config_path()
    temporary = encrypted.with_suffix(".tmp")
    temporary.write_bytes(_encrypt(data))
    temporary.replace(encrypted)


def config_file_is_encrypted() -> bool:
    return get_encrypted_config_path().exists()


def redact_config(data: dict[str, Any]) -> dict[str, Any]:
    redacted = dict(data)
    if "client_id" in redacted and redacted["client_id"]:
        redacted["client_id"] = "********"
    return redacted
