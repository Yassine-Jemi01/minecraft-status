from minecraft_status.minecraft_reader.locator import find_all_saves_dirs, find_launcher_instance_dirs, find_latest_world, find_vanilla_minecraft_dir


def main() -> None:
    print("=== Locator Test ===")
    print(f"Vanilla Minecraft: {find_vanilla_minecraft_dir()}")
    print("Launcher instances:")
    for path in find_launcher_instance_dirs():
        print(f"  {path}")
    print("Saves folders:")
    for path in find_all_saves_dirs():
        print(f"  {path}")
    print(f"Latest world: {find_latest_world()}")


if __name__ == "__main__":
    main()
