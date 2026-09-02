"""Standalone server helpers used by the thin Agent Box command group."""

from __future__ import annotations

import argparse
import json
import secrets
import socket
import threading
import time
import urllib.error
import urllib.request
import webbrowser

from .config import AppConfig
from .server_state import (
    ServerCredentials,
    clear_credentials,
    read_credentials,
    write_credentials,
)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = AppConfig.from_env().port


def server_url(port: int = DEFAULT_PORT, token: str | None = None) -> str:
    base = f"http://{DEFAULT_HOST}:{port}"
    return f"{base}/?token={token}" if token else base


def open_ui(port: int = DEFAULT_PORT) -> bool:
    credentials = read_credentials(port)
    return webbrowser.open(server_url(port, credentials.token))


def fetch_status(port: int = DEFAULT_PORT) -> dict:
    credentials = read_credentials(port)
    try:
        request = urllib.request.Request(
            f"{server_url(port)}/api/status",
            headers={"X-Meeting-Token": credentials.token},
        )
        with urllib.request.urlopen(request, timeout=2) as response:
            return json.load(response)
    except (urllib.error.URLError, TimeoutError) as error:
        raise RuntimeError(
            f"Meeting Assistant is not running at {server_url(port)}. "
            "Start it with `agb meeting start`."
        ) from error


def _reserve_port(port: int) -> socket.socket:
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((DEFAULT_HOST, port))
        listener.listen()
        return listener
    except OSError as error:
        listener.close()
        raise RuntimeError(
            f"Port {port} is already in use; the running server credentials were preserved."
        ) from error


def run_server(
    port: int = DEFAULT_PORT, *, open_browser: bool = True, token: str | None = None
) -> None:
    import uvicorn

    from .api import create_app

    listener = _reserve_port(port)
    credentials = ServerCredentials(port=port, token=token or secrets.token_urlsafe(32))
    try:
        write_credentials(credentials)
        if open_browser:
            threading.Thread(
                target=lambda: (
                    time.sleep(0.8),
                    webbrowser.open(server_url(port, credentials.token)),
                ),
                name="meeting-browser",
                daemon=True,
            ).start()
        config = uvicorn.Config(
            create_app(access_token=credentials.token),
            host=DEFAULT_HOST,
            port=port,
            log_level="info",
            access_log=False,
        )
        uvicorn.Server(config).run(sockets=[listener])
    finally:
        listener.close()
        clear_credentials(credentials)


def main() -> None:
    parser = argparse.ArgumentParser(description="Local meeting question assistant")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()
    run_server(args.port, open_browser=not args.no_open)


if __name__ == "__main__":
    main()
