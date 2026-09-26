from tests.helpers import fixture
from minecraft_status.minecraft_reader.advancements import get_achievements_summary


def main() -> None:
    summary = get_achievements_summary(fixture("modern_advancements.json"), fixture("modern_stats.json"))
    print(summary)


if __name__ == "__main__":
    main()
