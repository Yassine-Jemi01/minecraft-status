from __future__ import annotations

import errno
import os
import platform
from pathlib import Path

if os.name != "nt":
    import fcntl

KNOWN_LAUNCHER_NAMES = [
    "PrismLauncher",
    "ElyPrismLauncher",
    "MultiMC",
    "PolyMC",
    "GDLauncher",
]

INSTANCE_GAME_FOLDER_NAMES = [".minecraft", "minecraft"]


def find_vanilla_minecraft_dir() -> Path | None:
    system = platform.system()
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        if not appdata:
            return None
        candidate = Path(appdata) / ".minecraft"
    elif system == "Darwin":
        candidate = Path.home() / "Library/Application Support/minecraft"
    else:
        candidate = Path.home() / ".minecraft"
    return candidate if candidate.exists() else None


def _app_data_base_dir() -> Path:
    system = platform.system()
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        return Path(appdata) if appdata else Path.home()
    if system == "Darwin":
        return Path.home() / "Library/Application Support"
    xdg = os.environ.get("XDG_DATA_HOME")
    return Path(xdg) if xdg else Path.home() / ".local/share"


def find_launcher_instance_dirs() -> list[Path]:
    base = _app_data_base_dir()
    result: list[Path] = []
    for launcher in KNOWN_LAUNCHER_NAMES:
        root = base / launcher / "instances"
        if not root.exists():
            continue
        try:
            entries = root.iterdir()
        except OSError:
            continue
        result.extend(entry for entry in entries if entry.is_dir())
    return result


def find_all_saves_dirs() -> list[Path]:
    result: list[Path] = []
    vanilla = find_vanilla_minecraft_dir()
    if vanilla:
        saves = vanilla / "saves"
        if saves.exists():
            result.append(saves)

    for instance in find_launcher_instance_dirs():
        for folder in INSTANCE_GAME_FOLDER_NAMES:
            saves = instance / folder / "saves"
            if saves.exists():
                result.append(saves)
    return result


def _try_native_lock(path: Path) -> bool:
    """Return True when another process currently owns session.lock."""
    try:
        with path.open("r+b") as file:
            if os.name == "nt":
                import msvcrt
                try:
                    msvcrt.locking(file.fileno(), msvcrt.LK_NBLCK, 1)
                except OSError:
                    return True
                try:
                    file.seek(0)
                    msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, 1)
                except OSError:
                    pass
                return False

            try:
                fcntl.lockf(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                if exc.errno in (errno.EACCES, errno.EAGAIN):
                    return True
                return False
            finally:
                try:
                    fcntl.lockf(file, fcntl.LOCK_UN)
                except OSError:
                    pass
            return False
    except OSError:
        return False


def _is_world_active(world_dir: Path) -> bool:
    lock_path = world_dir / "session.lock"
    if not lock_path.exists():
        return False
    return _try_native_lock(lock_path)


def find_active_world() -> Path | None:
    for saves_dir in find_all_saves_dirs():
        try:
            worlds = list(saves_dir.iterdir())
        except OSError:
            continue
        for world in worlds:
            if not world.is_dir():
                continue
            if not (world / "level.dat").exists():
                continue
            if _is_world_active(world):
                return world
    return None


def find_latest_world() -> Path | None:
    candidates: list[tuple[float, Path]] = []
    for saves_dir in find_all_saves_dirs():
        try:
            worlds = list(saves_dir.iterdir())
        except OSError:
            continue
        for world in worlds:
            level_dat = world / "level.dat"
            if not world.is_dir() or not level_dat.exists():
                continue
            try:
                mtime = level_dat.stat().st_mtime
            except OSError:
                continue
            candidates.append((mtime, world))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]
