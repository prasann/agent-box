"""User-private credentials for discovering a running local server."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .storage import default_data_dir


@dataclass(frozen=True)
class ServerCredentials:
    port: int
    token: str


def credentials_path(port: int) -> Path:
    return default_data_dir() / f"server-{port}.json"


def write_credentials(credentials: ServerCredentials) -> None:
    path = credentials_path(credentials.port)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(
                {"port": credentials.port, "token": credentials.token},
                handle,
                separators=(",", ":"),
            )
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def read_credentials(port: int) -> ServerCredentials:
    path = credentials_path(port)
    try:
        value = json.loads(path.read_text())
        os.chmod(path, 0o600)
        return ServerCredentials(port=int(value["port"]), token=str(value["token"]))
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise RuntimeError(
            f"No access credentials found for the Meeting Assistant on port {port}. "
            "Start it with `agb meeting start`."
        ) from error


def clear_credentials(credentials: ServerCredentials) -> None:
    path = credentials_path(credentials.port)
    try:
        saved = read_credentials(credentials.port)
    except RuntimeError:
        return
    if saved.token == credentials.token:
        path.unlink(missing_ok=True)

