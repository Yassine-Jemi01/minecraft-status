from minecraft_status.minecraft_reader.biome import format_biome


def main() -> None:
    assert format_biome("minecraft:stony_shore") == "Stony Shore"
    print("Biome formatting passed.")


if __name__ == "__main__":
    main()
