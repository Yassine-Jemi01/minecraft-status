from __future__ import annotations

from pypresence import Presence
from pypresence.exceptions import (
    ConnectionTimeout,
    DiscordNotFound,
    InvalidID,
    InvalidPipe,
    PipeClosed,
    PyPresenceException,
    ResponseTimeout,
)


class DiscordPresence:
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.rpc: Presence | None = None

    @property
    def connected(self) -> bool:
        return self.rpc is not None

    @staticmethod
    def is_connection_error(exc: Exception) -> bool:
        return isinstance(
            exc,
            (
                DiscordNotFound,
                InvalidPipe,
                PipeClosed,
                ConnectionTimeout,
                ResponseTimeout,
                ConnectionError,
                BrokenPipeError,
                OSError,
            ),
        )

    def connect(self) -> None:
        if self.rpc is not None:
            return
        rpc = Presence(self.client_id)
        try:
            rpc.connect()
        except Exception:
            try:
                rpc.close()
            except Exception:
                pass
            raise
        self.rpc = rpc

    def disconnect(self) -> None:
        rpc = self.rpc
        self.rpc = None
        if rpc is not None:
            try:
                rpc.close()
            except Exception:
                pass

    def update(self, **kwargs) -> None:
        if self.rpc is None:
            raise RuntimeError("Discord Presence is not connected.")
        self.rpc.update(**kwargs)

    def clear(self) -> None:
        if self.rpc is None:
            return
        try:
            self.rpc.clear()
        except Exception as exc:
            if self.is_connection_error(exc):
                self.disconnect()
                return
            raise

    def close(self) -> None:
        self.disconnect()


def validate_client_id(client_id: str) -> None:
    rpc = None
    try:
        rpc = Presence(client_id)
        rpc.connect()
    except InvalidID as exc:
        raise ValueError("The Discord Client ID is invalid.") from exc
    except DiscordNotFound as exc:
        raise RuntimeError("Discord Desktop is not running.") from exc
    except PyPresenceException as exc:
        raise RuntimeError(f"Could not validate the Client ID with Discord: {exc}") from exc
    finally:
        if rpc is not None:
            try:
                rpc.close()
            except Exception:
                pass
