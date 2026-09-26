from __future__ import annotations

import argparse
import signal
import time

from . import config
from .autostart_manager import disable_autostart, enable_autostart, get_autostart_path, is_autostart_enabled
from .minecraft_reader.advancements import get_achievements_summary, get_matching_advancements_file
from .minecraft_reader.biome import format_biome, get_biome
from .minecraft_reader.discord_presence import DiscordPresence, validate_client_id
from .minecraft_reader.locator import find_active_world
from .minecraft_reader.player_data import (
    format_coordinates,
    format_dimension,
    get_player_data,
    get_world_day,
)
from .minecraft_reader.stats import format_playtime, get_latest_stats_file, get_playtime_seconds
from .process_manager import clear_logs, follow_logs, get_running_pid, read_logs, restart_background, start_background, stop_background
from .secure_store import config_file_is_encrypted, get_config_dir, redact_config
from .user_config import get_client_id, load_user_config, set_client_id, validate_client_id_format


def setup() -> None:
    current = get_client_id()
    print("Minecraft Status Setup")
    print()
    if current:
        print("A Discord Client ID is already configured.")
        value = input("Enter a new Client ID (press Enter to keep the current one): ").strip()
        if not value:
            print("Current Client ID kept.")
            return
    else:
        value = input("Enter your Discord Client ID: ").strip()
        if not value:
            print("No Client ID entered. Setup cancelled.")
            return

    if not validate_client_id_format(value):
        print("Setup failed: invalid Client ID format.")
        return

    print("Validating Client ID with Discord...")
    try:
        validate_client_id(value)
    except ValueError as exc:
        print(f"Setup failed: {exc}")
        return
    except RuntimeError as exc:
        print(f"Setup failed: {exc}")
        return

    set_client_id(value)
    print("Discord Client ID validated and saved.")
    print(f"Encrypted configuration directory: {get_config_dir()}")
    print("Auto-start remains unchanged; it is disabled by default.")


def change_client_id() -> None:
    value = input("Enter your new Discord Client ID: ").strip()
    if not validate_client_id_format(value):
        print("Invalid Client ID format.")
        return
    try:
        validate_client_id(value)
        set_client_id(value)
    except (ValueError, RuntimeError) as exc:
        print(f"Could not update Client ID: {exc}")
        return
    print("Discord Client ID updated successfully.")


def build_presence_data(world):
    stats_file = get_latest_stats_file(world)
    achievements = {"total_done": 0, "first_achievement": None, "latest_achievement": None}
    playtime_seconds = 0

    if stats_file is not None:
        try:
            playtime_seconds = get_playtime_seconds(stats_file)
        except (OSError, ValueError, TypeError):
            pass

        adv_file = get_matching_advancements_file(world, stats_file)
        try:
            achievements = get_achievements_summary(adv_file, stats_file)
        except (OSError, ValueError, TypeError):
            pass

    player_data = get_player_data(world)
    biome = None
    if player_data is not None:
        try:
            biome = get_biome(world, player_data)
        except (OSError, ValueError, TypeError):
            pass

    return {
        "world_name": world.name,
        "achievements": achievements,
        "playtime_seconds": playtime_seconds,
        "world_day": get_world_day(world),
        "player_data": player_data,
        "biome": biome,
    }


def _details(data: dict, user_config: dict) -> str:
    details = data["world_name"]

    if user_config.get("show_total_playtime", True):
        details = f"{details} • {format_playtime(data['playtime_seconds'])}"

    return details[:128]


def _state(data: dict, user_config: dict) -> str:
    parts: list[str] = []
    player = data["player_data"]

    if player is not None:
        parts.append(format_dimension(player))

        if user_config.get("show_biome", True) and data["biome"]:
            parts.append(format_biome(data["biome"]))

        if user_config.get("show_coordinates", True):
            parts.append(format_coordinates(player))

    world_day = data.get("world_day")
    if world_day is not None:
        parts.append(f"Day {world_day}")

    return " • ".join(parts)[:128] if parts else "Playing Minecraft"


def _large_text(data: dict, user_config: dict) -> str:
    player = data["player_data"]
    if user_config.get("show_coordinates", True) and player is not None:
        return f"Coordinates: {format_coordinates(player)}"[:128]
    return str(user_config.get("large_image_text", config.LARGE_IMAGE_TEXT))[:128]


def _small_text(data: dict, user_config: dict) -> str:
    if user_config.get("show_latest_achievement", True):
        latest = data["achievements"].get("latest_achievement")
        total = int(data["achievements"].get("total_done") or 0)

        if latest and total:
            return f"Latest: {latest} • {total} advancements"[:128]
        if latest:
            return f"Latest: {latest}"[:128]
        if total:
            return f"Advancements: {total}"[:128]

    return str(user_config.get("small_image_text", config.SMALL_IMAGE_TEXT))[:128]


def run() -> None:
    client_id = get_client_id()
    if not client_id:
        raise RuntimeError("No Discord Client ID is configured. Run 'minecraft-status setup' first.")

    user_config = load_user_config()
    presence = DiscordPresence(client_id)
    session_world = None
    session_start = None

    def stop_signal(_signum, _frame) -> None:
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, stop_signal)

    try:
        while True:
            if not presence.connected:
                print("Discord is not connected. Trying to connect...", flush=True)
                try:
                    presence.connect()
                    print("Connected to Discord.", flush=True)
                except Exception as exc:
                    print(f"Could not connect to Discord: {exc}", flush=True)
                    time.sleep(float(user_config.get("reconnect_interval", config.RECONNECT_INTERVAL)))
                    continue

            try:
                world = find_active_world()
                if world is None:
                    if session_world is not None:
                        print("Minecraft world closed.", flush=True)
                    session_world = None
                    session_start = None
                    presence.clear()
                else:
                    if world != session_world:
                        session_world = world
                        session_start = int(time.time())
                        print(f"Minecraft session started: {world.name}", flush=True)
                    data = build_presence_data(world)
                    presence.update(
                        details=_details(data, user_config),
                        state=_state(data, user_config),
                        large_image=user_config.get("large_image", config.LARGE_IMAGE),
                        large_text=_large_text(data, user_config),
                        small_image=user_config.get("small_image", config.SMALL_IMAGE),
                        small_text=_small_text(data, user_config),
                        start=session_start if user_config.get("show_session_time", True) else None,
                    )
                    print(
                        f"World: {data['world_name']} | "
                        f"Details: {_details(data, user_config)} | "
                        f"State: {_state(data, user_config)}",
                        flush=True,
                    )
            except Exception as exc:
                if presence.is_connection_error(exc):
                    print("Discord connection was lost. Will reconnect.", flush=True)
                    presence.disconnect()
                else:
                    print(f"Update cycle failed: {exc}", flush=True)

            time.sleep(float(user_config.get("update_interval", config.UPDATE_INTERVAL)))
    except KeyboardInterrupt:
        print("\nStopping...", flush=True)
    finally:
        try:
            presence.clear()
        except Exception:
            pass
        presence.close()


def show_status() -> None:
    pid = get_running_pid()
    if pid is None:
        print("Minecraft Status is not running.")
    else:
        print(f"Minecraft Status is running (PID {pid}).")
    print(f"Auto-start: {'enabled' if is_autostart_enabled() else 'disabled'}")
    print(f"Encrypted config: {'yes' if config_file_is_encrypted() else 'not created'}")


def handle_autostart(action: str | None) -> None:
    if action == "enable":
        try:
            path = enable_autostart()
        except RuntimeError as exc:
            print(f"Failed to enable auto-start: {exc}")
            return
        print("Auto-start enabled.")
        print("Minecraft Status will start automatically when you log in.")
        print(f"Startup entry: {path}")
        return
    if action == "disable":
        try:
            removed = disable_autostart()
        except RuntimeError as exc:
            print(f"Failed to disable auto-start: {exc}")
            return
        print("Auto-start disabled." if removed else "Auto-start is already disabled.")
        return
    if action == "status":
        if is_autostart_enabled():
            print("Auto-start is enabled.")
            print(f"Startup entry: {get_autostart_path()}")
        else:
            print("Auto-start is disabled.")
        return
    print("Usage: minecraft-status autostart {enable|disable|status}")


def handle_config(action: str | None) -> None:
    if action == "client-id":
        change_client_id()
        return
    if action == "show":
        print(redact_config(load_user_config()))
        return
    print("Usage: minecraft-status config {client-id|show}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Minecraft Java Edition Discord Rich Presence")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("setup", help="Configure Discord Client ID")
    sub.add_parser("start", help="Start in the background")
    sub.add_parser("stop", help="Stop the background process")
    sub.add_parser("restart", help="Restart the background process")
    sub.add_parser("status", help="Show current status")

    logs = sub.add_parser("logs", help="View logs")
    logs.add_argument("-n", "--lines", type=int, default=50)
    logs.add_argument("-f", "--follow", action="store_true")
    logs.add_argument("--clear", action="store_true")

    auto = sub.add_parser("autostart", help="Control automatic startup")
    auto.add_argument("action", nargs="?", choices=["enable", "disable", "status"])

    cfg = sub.add_parser("config", help="Manage user configuration")
    cfg.add_argument("action", nargs="?", choices=["client-id", "show"])

    sub.add_parser("run", help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.command == "setup":
        setup()
    elif args.command == "config":
        handle_config(args.action)
    elif args.command == "start":
        try:
            print(f"Minecraft Status started in the background (PID {start_background()}).")
        except RuntimeError as exc:
            print(f"Failed to start: {exc}")
    elif args.command == "stop":
        print("Minecraft Status stopped." if stop_background() else "Minecraft Status is not running.")
    elif args.command == "restart":
        try:
            old_pid, new_pid = restart_background()
            if old_pid is not None:
                print(f"Minecraft Status stopped (PID {old_pid}).")
            print(f"Minecraft Status started in the background (PID {new_pid}).")
        except RuntimeError as exc:
            print(f"Failed to restart: {exc}")
    elif args.command == "status":
        show_status()
    elif args.command == "logs":
        if args.lines <= 0:
            print("Error: --lines must be greater than zero.")
        elif args.clear:
            try:
                clear_logs()
                print("Logs cleared.")
            except RuntimeError as exc:
                print(exc)
        elif args.follow:
            follow_logs(args.lines)
        else:
            print(read_logs(args.lines))
    elif args.command == "autostart":
        handle_autostart(args.action)
    elif args.command == "run":
        run()
    else:
        run()


if __name__ == "__main__":
    main()
