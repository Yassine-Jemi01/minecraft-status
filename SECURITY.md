# Security and privacy

## Local secrets

Minecraft Status stores its user configuration in an encrypted local file. The encryption key is kept in the operating-system credential store when available, with a restrictive local-key fallback when an OS credential store is unavailable.

The following files must never be committed:

- `config.enc`
- `secret.key`
- runtime logs
- PID files
- local Minecraft save data

The repository `.gitignore` already excludes these paths and file patterns.

## Discord Client ID

A Discord Client ID is an application identifier, not a Discord account password or bot token. Minecraft Status still treats it as user configuration and keeps it out of source control.

## Reporting a security problem

Please do not publish private configuration files, encryption keys, local Minecraft worlds, or logs in an issue.

Open a private security report through the repository's security contact when available.
