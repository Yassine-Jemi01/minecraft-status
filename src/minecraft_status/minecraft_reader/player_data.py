from __future__ import annotations

import struct
from pathlib import Path
from uuid import UUID

import nbtlib


def _format_uuid(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        try:
            return str(UUID(value))
        except ValueError:
            return None
    try:
        values = [int(item) for item in value]
    except (TypeError, ValueError):
        return None
    try:
        if len(values) == 4:
            return str(UUID(bytes=b"".join(struct.pack(">i", x) for x in values)))
        if len(values) == 2:
            return str(UUID(bytes=b"".join(struct.pack(">q", x) for x in values)))
    except (struct.error, ValueError):
        return None
    return None


def _read_level_data(world_dir: Path):
    level_dat = world_dir / "level.dat"
    if not level_dat.exists():
        return None
    try:
        return nbtlib.load(level_dat).get("Data")
    except (OSError, ValueError, TypeError):
        return None


def get_world_day(world_dir: Path) -> int | None:
    data = _read_level_data(world_dir)
    if data is None:
        return None

    for key in ("Time", "time"):
        value = data.get(key)
        try:
            ticks = int(value)
        except (TypeError, ValueError):
            continue
        return max(0, ticks) // 24000

    return None


def get_singleplayer_uuid(world_dir: Path) -> str | None:
    data = _read_level_data(world_dir)
    if data is None:
        return None
    value = _format_uuid(data.get("singleplayer_uuid"))
    if value:
        return value
    player = data.get("Player")
    if player is not None:
        return _format_uuid(player.get("UUID"))
    return None


def _extract_player_data(player) -> dict | None:
    if player is None:
        return None
    pos = player.get("Pos")
    dimension = player.get("Dimension")
    if pos is None or len(pos) < 3:
        return None
    try:
        x, y, z = float(pos[0]), float(pos[1]), float(pos[2])
    except (TypeError, ValueError):
        return None

    try:
        numeric = int(dimension)
    except (TypeError, ValueError):
        dimension_value = str(dimension) if dimension is not None else "unknown"
    else:
        dimension_value = {
            -1: "minecraft:the_nether",
            0: "minecraft:overworld",
            1: "minecraft:the_end",
        }.get(numeric, str(numeric))

    return {"dimension": dimension_value, "x": x, "y": y, "z": z}


def _find_player_file(world_dir: Path) -> Path | None:
    uuid = get_singleplayer_uuid(world_dir)
    if uuid:
        modern = world_dir / "players/data" / f"{uuid}.dat"
        if modern.exists():
            return modern
        legacy = world_dir / "playerdata" / f"{uuid}.dat"
        if legacy.exists():
            return legacy

    legacy_dir = world_dir / "playerdata"
    if legacy_dir.exists():
        files = list(legacy_dir.glob("*.dat"))
        if len(files) == 1:
            return files[0]

    old_dir = world_dir / "players"
    if old_dir.exists():
        files = [p for p in old_dir.glob("*.dat") if p.is_file()]
        if len(files) == 1:
            return files[0]
    return None


def get_player_data(world_dir: Path) -> dict | None:
    data = _read_level_data(world_dir)
    if data is None:
        return None

    embedded = data.get("Player")
    if embedded is not None:
        result = _extract_player_data(embedded)
        if result is not None:
            return result

    player_file = _find_player_file(world_dir)
    if player_file is None:
        return None
    try:
        return _extract_player_data(nbtlib.load(player_file))
    except (OSError, ValueError, TypeError):
        return None


def format_coordinates(player_data: dict | None) -> str:
    if player_data is None:
        return "Unknown"
    return (
        f"X {player_data['x']:.1f}, "
        f"Y {player_data['y']:.1f}, "
        f"Z {player_data['z']:.1f}"
    )


def format_dimension(player_data: dict | None) -> str:
    if player_data is None:
        return "Unknown"
    dimension = player_data.get("dimension", "unknown")
    if isinstance(dimension, int):
        return {-1: "The Nether", 0: "Overworld", 1: "The End"}.get(
            dimension, str(dimension)
        )
    return {
        "minecraft:overworld": "Overworld",
        "minecraft:the_nether": "The Nether",
        "minecraft:the_end": "The End",
    }.get(str(dimension), str(dimension))
