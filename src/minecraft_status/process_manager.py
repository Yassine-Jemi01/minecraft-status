from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from .secure_store import get_config_dir

PID_FILE = get_config_dir() / "minecraft-status.pid"
LOG_FILE = get_config_dir() / "minecraft-status.log"


def _ensure_dir() -> None:
    get_config_dir().mkdir(parents=True, exist_ok=True)


def _read_pid() -> int | None:
    if not PID_FILE.exists():
        return None
    try:
        return int(PID_FILE.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def _write_pid(pid: int) -> None:
    _ensure_dir()
    PID_FILE.write_text(str(pid), encoding="utf-8")


def _remove_pid() -> None:
    try:
        PID_FILE.unlink()
    except (FileNotFoundError, OSError):
        pass


def _is_running(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
            capture_output=True,
            text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return str(pid) in result.stdout
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def get_running_pid() -> int | None:
    pid = _read_pid()
    if pid is None:
        return None
    if _is_running(pid):
        return pid
    _remove_pid()
    return None


def start_background() -> int:
    existing = get_running_pid()
    if existing is not None:
        raise RuntimeError(f"Minecraft Status is already running (PID {existing}).")
    _ensure_dir()
    log = LOG_FILE.open("a", encoding="utf-8")
    command = [sys.executable, "-u", "-m", "minecraft_status", "run"]
    try:
        if os.name == "nt":
            flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            process = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                creationflags=flags,
                close_fds=True,
            )
        else:
            process = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                close_fds=True,
            )
    finally:
        log.close()
    _write_pid(process.pid)
    time.sleep(0.2)
    if not _is_running(process.pid):
        _remove_pid()
        raise RuntimeError(f"Minecraft Status exited immediately. Check {LOG_FILE}")
    return process.pid


def stop_background() -> bool:
    pid = get_running_pid()
    if pid is None:
        return False
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            capture_output=True,
            text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    else:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        for _ in range(30):
            if not _is_running(pid):
                break
            time.sleep(0.1)
        if _is_running(pid):
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    _remove_pid()
    return True


def restart_background() -> tuple[int | None, int]:
    old_pid = get_running_pid()
    if old_pid is not None:
        stop_background()
    return old_pid, start_background()


def clear_logs() -> None:
    _ensure_dir()
    try:
        LOG_FILE.write_text("", encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"Could not clear log file: {exc}") from exc


def read_logs(lines: int = 50) -> str:
    if lines <= 0:
        raise ValueError("Number of lines must be greater than zero.")
    if not LOG_FILE.exists():
        return "No logs available yet."
    try:
        content = LOG_FILE.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return f"Could not read logs: {exc}"
    all_lines = content.splitlines()
    return "\n".join(all_lines[-lines:]) if all_lines else "No logs available yet."


def follow_logs(lines: int = 20) -> None:
    print(read_logs(lines))
    print("\nFollowing logs... Press Ctrl+C to stop.")
    position = LOG_FILE.stat().st_size if LOG_FILE.exists() else 0
    try:
        while True:
            if LOG_FILE.exists():
                try:
                    with LOG_FILE.open("r", encoding="utf-8", errors="replace") as handle:
                        handle.seek(position)
                        chunk = handle.read()
                        position = handle.tell()
                    if chunk:
                        print(chunk, end="", flush=True)
                except OSError:
                    pass
            time.sleep(0.25)
    except KeyboardInterrupt:
        print("\nStopped following logs.")
