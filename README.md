# Minecraft Status

Minecraft Status is a cross-platform Python application that reads local Minecraft Java Edition world data and publishes a Discord Rich Presence.

It is designed for Windows, macOS, and Linux, and it supports background operation, Discord reconnects, optional auto-start, encrypted local user configuration, and multiple Minecraft save formats.

## Features

- Discord Rich Presence for Minecraft Java Edition
- Detects active worlds from Minecraft's `session.lock`
- Current-session elapsed timer instead of total world playtime
- World name as the main Presence detail
- Dimension and biome in the Presence state
- Coordinates shown through the large image tooltip
- Latest achievement/advancement shown through the small image tooltip when available
- Automatic Discord reconnect after Discord closes or restarts
- `start`, `stop`, `restart`, `status`, and `logs`
- `setup` and `config client-id` for Client ID management without editing source files
- Auto-start is disabled by default and must be explicitly enabled
- Cross-platform auto-start support for Linux, macOS, and Windows
- User configuration is encrypted locally; the repository never contains the user's Client ID or encryption key
- Legacy stats/achievement support and modern advancement support
- 26.1+ world layout support, including `players/` storage and `dimensions/` storage

## Requirements

- Python 3.9+
- Minecraft Java Edition
- Discord Desktop
- A Discord application with Rich Presence assets

`pypresence` currently supports Python 3.9 and newer. See its documentation for current package information.

## Installation from source

Clone the repository and create a virtual environment:

```bash
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\\Scripts\\Activate.ps1
```

Install the package:

```bash
python -m pip install -U pip
python -m pip install -e .
```

For development:

```bash
python -m pip install -e '.[dev]'
```

Optional OS credential-store integration:

```bash
python -m pip install -e '.[keyring]'
```

## Discord setup

Create a Discord application at:

https://discord.com/developers/applications

Upload Rich Presence assets in the application and note their asset keys. The defaults in the project expect:

- `minecraft` for the large image
- `minecraft` for the small image

The application uses the Discord desktop client's local IPC connection. Your Discord Client ID is stored locally and is not included in this repository.

## First run

Configure the Client ID once:

```bash
minecraft-status setup
```

The application validates the ID through Discord before saving it.

To change it later:

```bash
minecraft-status config client-id
```

The stored configuration is encrypted locally. When an OS credential store is available, the encryption key is kept there. Otherwise a local key file with restrictive permissions is used as a fallback. The encrypted configuration and key are ignored by Git.

## Running

Start in the background:

```bash
minecraft-status start
```

Check the process:

```bash
minecraft-status status
```

Stop it:

```bash
minecraft-status stop
```

Restart it:

```bash
minecraft-status restart
```

Run in the foreground for development:

```bash
minecraft-status run
```

## Logs

Show recent logs:

```bash
minecraft-status logs
```

Show 100 lines:

```bash
minecraft-status logs --lines 100
```

Follow logs live:

```bash
minecraft-status logs --follow
```

Clear the log:

```bash
minecraft-status logs --clear
```

## Auto-start

Auto-start is **disabled by default**.

Enable it explicitly:

```bash
minecraft-status autostart enable
```

Disable it:

```bash
minecraft-status autostart disable
```

Check it:

```bash
minecraft-status autostart status
```

Auto-start does not start Minecraft itself. It only starts Minecraft Status when you log into your operating system.

## Privacy and local data

Minecraft Status reads local Minecraft save data only to build the Presence shown in Discord.

The application does not upload the user's Client ID or local Minecraft files to a project server.

The local configuration file is encrypted. The repository contains no user configuration, encryption key, PID file, or runtime logs.

Rich Presence itself is visible on Discord according to Discord's activity/privacy behavior.

## Minecraft format compatibility

The reader is structured around the actual world layout instead of assuming one release format.

Covered layouts include:

- UUID-based `playerdata/<uuid>.dat`
- modern 26.1+ `players/data/<uuid>.dat`
- legacy `Data.Player` fallback
- legacy `stats/<uuid>.json`
- modern 26.1+ `players/stats/<uuid>.json`
- legacy `achievement.*` entries
- 1.12+ advancement JSON files
- modern 26.1+ `players/advancements/<uuid>.json`
- pre-1.18 biome storage
- 1.18+ section biome palettes
- pre-1.13 biome IDs
- modern and legacy dimension identifiers

Minecraft 26.1 introduced a major world-storage change: default dimensions moved under `dimensions/minecraft/...`, and player storage moved under `players/`. The reader explicitly handles those paths.

This project tests real 26.x data through fixtures and supports older layouts by parser compatibility. Real older-version world fixtures should be added before claiming a specific older version is fully integration-tested.

## Tests

Run the included test runner:

```bash
python -m tests.run_all
```

Or use pytest:

```bash
pytest
```

The `tests/fixtures/` directory contains small synthetic JSON samples for legacy and modern stats/advancements so format compatibility can be tested without launching Minecraft.

## Project layout

```text
minecraft-status/
├── src/
│   └── minecraft_status/
│       ├── main.py
│       ├── config.py
│       ├── user_config.py
│       ├── secure_store.py
│       ├── process_manager.py
│       ├── autostart_manager.py
│       └── minecraft_reader/
├── tests/
│   └── fixtures/
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── README.md
├── LICENSE
└── .gitignore
```

## License

This project is licensed under the GNU General Public License v3.0 or later. See `LICENSE`.
