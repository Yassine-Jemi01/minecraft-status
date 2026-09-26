# Contributing

1. Keep user data out of the repository.
2. Do not commit `config.enc`, `secret.key`, logs, PIDs, or local Minecraft files.
3. Add or update synthetic fixtures when changing format parsers.
4. Run `python -m tests.run_all` before submitting changes.
5. Keep platform-specific behavior behind dedicated modules.
