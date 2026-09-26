from __future__ import annotations

import os
from tempfile import TemporaryDirectory

from minecraft_status.secure_store import get_encrypted_config_path, load_config, save_config


def test_encrypted_round_trip() -> None:
    with TemporaryDirectory() as temp_dir:
        os.environ["MINECRAFT_STATUS_CONFIG_DIR"] = temp_dir
        save_config({"client_id": "123456789012345678", "answer": "secret"})
        path = get_encrypted_config_path()
        raw = path.read_bytes()
        assert b"123456789012345678" not in raw
        assert b"secret" not in raw
        assert load_config()["answer"] == "secret"
        os.environ.pop("MINECRAFT_STATUS_CONFIG_DIR", None)


def main() -> None:
    test_encrypted_round_trip()
    print("Secure store passed.")


if __name__ == "__main__":
    main()
