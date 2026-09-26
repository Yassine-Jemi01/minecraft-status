from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .stats import get_legacy_achievements


def get_matching_advancements_file(
    world_dir: Path,
    stats_file: Path | None,
) -> Path | None:
    if stats_file is None:
        return None
    uuid = stats_file.stem
    modern = world_dir / "players/advancements" / f"{uuid}.json"
    if modern.exists():
        return modern
    legacy = world_dir / "advancements" / f"{uuid}.json"
    if legacy.exists():
        return legacy
    return None


def _format_name(advancement_id: str) -> str:
    path = advancement_id.split(":", 1)[-1]
    if "/" in path:
        category, leaf = path.split("/", 1)
    else:
        category, leaf = "", path

    def clean(value: str) -> str:
        return value.replace("_", " ").replace("-", " ").title()

    return f"{clean(category)}: {clean(leaf)}" if category else clean(leaf)


def _parse_modern(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    result = {"total_done": 0, "first_achievement": None, "latest_achievement": None}
    if not isinstance(data, dict):
        return result
    completed = []
    for advancement_id, value in data.items():
        if advancement_id == "DataVersion":
            continue
        if not isinstance(value, dict) or not value.get("done"):
            continue
        timestamps = []
        for stamp in value.get("criteria", {}).values():
            try:
                timestamps.append(datetime.strptime(stamp, "%Y-%m-%d %H:%M:%S %z"))
            except (ValueError, TypeError):
                continue
        if timestamps:
            completed.append((max(timestamps), _format_name(advancement_id)))
    result["total_done"] = len(completed)
    if completed:
        completed.sort(key=lambda item: item[0])
        result["first_achievement"] = completed[0][1]
        result["latest_achievement"] = completed[-1][1]
    return result


def _parse_legacy(stats_file: Path) -> dict:
    legacy = get_legacy_achievements(stats_file)
    return {
        "total_done": len(legacy),
        "first_achievement": None,
        "latest_achievement": None,
    }


def get_achievements_summary(
    adv_file: Path | None,
    stats_file: Path | None = None,
) -> dict:
    result = {"total_done": 0, "first_achievement": None, "latest_achievement": None}
    if adv_file is not None and adv_file.exists():
        try:
            return _parse_modern(adv_file)
        except (OSError, ValueError, TypeError):
            return result
    if stats_file is not None and stats_file.exists():
        try:
            return _parse_legacy(stats_file)
        except (OSError, ValueError, TypeError):
            return result
    return result
