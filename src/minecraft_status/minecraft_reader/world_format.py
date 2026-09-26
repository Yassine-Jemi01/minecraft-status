from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import nbtlib


@dataclass(frozen=True)
class WorldFormat:
    data_version: int | None
    split_player_storage: bool
    split_dimension_storage: bool

    @property
    def family(self) -> str:
        if self.split_player_storage or self.split_dimension_storage:
            return "modern"
        return "legacy"


def _read_level_data(world_dir: Path):
    level_dat = world_dir / "level.dat"
    if not level_dat.exists():
        return None
    try:
        nbt = nbtlib.load(level_dat)
    except (OSError, ValueError, TypeError):
        return None
    return nbt.get("Data")


def get_data_version(world_dir: Path) -> int | None:
    data = _read_level_data(world_dir)
    if data is None:
        return None
    value = data.get("DataVersion")
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def detect_world_format(world_dir: Path) -> WorldFormat:
    data = _read_level_data(world_dir)
    data_version = None
    if data is not None:
        value = data.get("DataVersion")
        try:
            data_version = int(value) if value is not None else None
        except (TypeError, ValueError):
            pass

    players_dir = world_dir / "players"
    dimensions_dir = world_dir / "dimensions"

    split_player_storage = players_dir.is_dir() or (
        data is not None and data.get("singleplayer_uuid") is not None
    )

    split_dimension_storage = dimensions_dir.is_dir() and any(
        (
            dimensions_dir / "minecraft" / child
        ).exists()
        for child in ("overworld", "the_nether", "the_end")
    )

    return WorldFormat(
        data_version=data_version,
        split_player_storage=split_player_storage,
        split_dimension_storage=split_dimension_storage,
    )
