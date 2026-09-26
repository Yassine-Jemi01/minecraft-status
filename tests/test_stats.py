from tests.helpers import fixture
from minecraft_status.minecraft_reader.stats import get_playtime_seconds


def main() -> None:
    print(f"Fixture playtime: {get_playtime_seconds(fixture('modern_stats.json'))} seconds")


if __name__ == "__main__":
    main()
