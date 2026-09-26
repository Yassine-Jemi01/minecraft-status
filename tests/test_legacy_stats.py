from tests.helpers import fixture
from minecraft_status.minecraft_reader.advancements import get_achievements_summary
from minecraft_status.minecraft_reader.stats import get_legacy_achievements, get_playtime_seconds


def test_legacy_stats_fixture() -> None:
    path = fixture("legacy_stats.json")
    assert get_playtime_seconds(path) == 200
    achievements = get_legacy_achievements(path)
    assert len(achievements) == 4
    summary = get_achievements_summary(None, path)
    assert summary["total_done"] == 4
    assert summary["latest_achievement"] is None


def main() -> None:
    test_legacy_stats_fixture()
    print("Legacy stats fixture passed.")


if __name__ == "__main__":
    main()
