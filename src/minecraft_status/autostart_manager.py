from __future__ import annotations

import os
import plistlib
import platform
from pathlib import Path

from .secure_store import get_config_dir
from .user_config import get_client_id

APP_LABEL = "com.minecraft-status"
APP_NAME = "Minecraft Status"


def _python_command() -> list[str]:
    return [os.path.abspath(os.sys.executable), "-m", "minecraft_status", "start"]


def _linux_path() -> Path:
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return config_home / "autostart" / "minecraft-status.desktop"


def _macos_path() -> Path:
    return Path.home() / "Library/LaunchAgents" / f"{APP_LABEL}.plist"


def _windows_path() -> Path:
    appdata = os.environ.get("APPDATA")
    base = Path(appdata) if appdata else Path.home() / "AppData/Roaming"
    return base / "Microsoft/Windows/Start Menu/Programs/Startup/Minecraft Status.vbs"


def get_autostart_path() -> Path:
    system = platform.system()
    if system == "Linux":
        return _linux_path()
    if system == "Darwin":
        return _macos_path()
    if system == "Windows":
        return _windows_path()
    raise RuntimeError(f"Unsupported operating system: {system}")


def is_autostart_enabled() -> bool:
    return get_autostart_path().exists()


def _enable_linux() -> Path:
    path = _linux_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    python = f'"{os.path.abspath(os.sys.executable)}"'
    path.write_text(
        "[Desktop Entry]\n"
        "Type=Application\n"
        f"Name={APP_NAME}\n"
        "Comment=Minecraft Discord Rich Presence\n"
        f"Exec={python} -m minecraft_status start\n"
        "Terminal=false\n"
        "X-GNOME-Autostart-enabled=true\n",
        encoding="utf-8",
    )
    return path


def _enable_macos() -> Path:
    path = _macos_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    plist = {
        "Label": APP_LABEL,
        "ProgramArguments": _python_command(),
        "WorkingDirectory": str(Path.home()),
        "RunAtLoad": True,
    }
    with path.open("wb") as handle:
        plistlib.dump(plist, handle, fmt=plistlib.FMT_XML, sort_keys=False)
    return path


def _enable_windows() -> Path:
    path = _windows_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    python = os.path.abspath(os.sys.executable)
    command = f'"{python}" -m minecraft_status start'
    content = (
        'Set shell = CreateObject("WScript.Shell")\n'
        f'shell.Run "{command.replace(chr(34), chr(34) + chr(34))}", 0, False\n'
    )
    path.write_text(content, encoding="utf-8")
    return path


def enable_autostart() -> Path:
    if not get_client_id():
        raise RuntimeError("No Discord Client ID is configured. Run 'minecraft-status setup' first.")
    system = platform.system()
    if system == "Linux":
        return _enable_linux()
    if system == "Darwin":
        return _enable_macos()
    if system == "Windows":
        return _enable_windows()
    raise RuntimeError(f"Unsupported operating system: {system}")


def disable_autostart() -> bool:
    path = get_autostart_path()
    if not path.exists():
        return False
    try:
        path.unlink()
    except OSError as exc:
        raise RuntimeError(f"Could not disable auto-start: {exc}") from exc
    return True
