from tests.helpers import fixture
from minecraft_status.minecraft_reader.advancements import get_achievements_summary
from minecraft_status.minecraft_reader.stats import get_playtime_seconds


def test_modern_fixtures() -> None:
    stats = fixture("modern_stats.json")
    advancements = fixture("modern_advancements.json")
    assert get_playtime_seconds(stats) == 300
    summary = get_achievements_summary(advancements, stats)
    assert summary["total_done"] == 2
    assert summary["first_achievement"] == "Minecraft"
    assert summary["latest_achievement"] == "Stone Age"


def main() -> None:
    test_modern_fixtures()
    print("Modern fixture passed.")


if __name__ == "__main__":
    main()
