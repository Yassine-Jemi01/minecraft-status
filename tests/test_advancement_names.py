from minecraft_status.minecraft_reader.advancement_names import (
    LEGACY_ACHIEVEMENT_TITLES,
    VANILLA_ADVANCEMENT_TITLES,
)
from minecraft_status.minecraft_reader.advancements import _format_name
from minecraft_status.minecraft_reader.stats import _format_legacy_achievement_name


def main() -> None:
    assert VANILLA_ADVANCEMENT_TITLES["minecraft:story/lava_bucket"] == "Hot Stuff"
    assert VANILLA_ADVANCEMENT_TITLES["minecraft:story/mine_stone"] == "Stone Age"
    assert _format_name("minecraft:story/lava_bucket") == "Hot Stuff"

    assert LEGACY_ACHIEVEMENT_TITLES["achievement.openInventory"] == "Taking Inventory"
    assert _format_legacy_achievement_name("achievement.openInventory") == "Taking Inventory"

    print("Vanilla advancement/achievement names: OK")


if __name__ == "__main__":
    main()
