from __future__ import annotations

import json
from pathlib import Path

from .player_data import get_singleplayer_uuid


def _load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def _stats_container(data: dict) -> dict:
    stats = data.get("stats")
    return stats if isinstance(stats, dict) else data


def get_latest_stats_file(world_dir: Path) -> Path | None:
    uuid = get_singleplayer_uuid(world_dir)
    modern_dir = world_dir / "players/stats"
    legacy_dir = world_dir / "stats"

    if uuid:
        modern = modern_dir / f"{uuid}.json"
        if modern.exists():
            return modern
        legacy = legacy_dir / f"{uuid}.json"
        if legacy.exists():
            return legacy

    if legacy_dir.exists():
        files = list(legacy_dir.glob("*.json"))
        if files:
            files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            return files[0]
    return None


def _number(value) -> int | None:
    if isinstance(value, dict):
        value = value.get("value")
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def get_playtime_ticks(stats_file: Path) -> int:
    data = _stats_container(_load(stats_file))
    custom = data.get("minecraft:custom")
    if isinstance(custom, dict):
        for key in ("minecraft:play_time", "minecraft:play_one_minute"):
            value = _number(custom.get(key))
            if value is not None:
                return value
    for key in (
        "stat.playOneMinute",
        "stat.play_time",
        "minecraft:play_one_minute",
        "minecraft:play_time",
    ):
        value = _number(data.get(key))
        if value is not None:
            return value
    return 0


def get_playtime_seconds(stats_file: Path) -> int:
    return get_playtime_ticks(stats_file) // 20


def format_playtime(seconds: int) -> str:
    days, remainder = divmod(max(0, seconds), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes = remainder // 60

    if days:
        return f"{days}d {hours}h {minutes}m"
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def _format_legacy_achievement_name(key: str) -> str:
    name = key[len("achievement."):]
    out: list[str] = []
    word = ""
    for char in name:
        if char == "_":
            if word:
                out.append(word)
                word = ""
            continue
        if char.isupper() and word:
            out.append(word)
            word = char.lower()
        else:
            word += char
    if word:
        out.append(word)
    return " ".join(item.title() for item in out)


def get_legacy_achievements(stats_file: Path) -> dict[str, int]:
    data = _stats_container(_load(stats_file))
    result: dict[str, int] = {}
    for key, value in data.items():
        if not isinstance(key, str) or not key.startswith("achievement."):
            continue
        number = _number(value)
        if number is None or number <= 0:
            continue
        result[_format_legacy_achievement_name(key)] = number
    return result
