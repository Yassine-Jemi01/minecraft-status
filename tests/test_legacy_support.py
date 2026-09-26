from minecraft_status.minecraft_reader.legacy_biomes import get_legacy_biome, get_pre_flattening_biome
from minecraft_status.minecraft_reader.player_data import format_dimension


def test_legacy_mappings() -> None:
    assert get_legacy_biome(1) == "minecraft:plains"
    assert get_legacy_biome(25) == "minecraft:stone_shore"
    assert get_pre_flattening_biome(3) == "minecraft:extreme_hills"
    assert get_pre_flattening_biome(8) == "minecraft:hell"
    assert format_dimension({"dimension": -1}) == "The Nether"
    assert format_dimension({"dimension": 0}) == "Overworld"
    assert format_dimension({"dimension": 1}) == "The End"


def main() -> None:
    test_legacy_mappings()
    print("Legacy support passed.")


if __name__ == "__main__":
    main()
