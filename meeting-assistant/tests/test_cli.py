import socket

import pytest

from meeting_assistant.cli import DEFAULT_HOST, _reserve_port, run_server
from meeting_assistant.server_state import (
    ServerCredentials,
    clear_credentials,
    read_credentials,
    write_credentials,
)


def test_duplicate_start_preserves_live_server_credentials(tmp_path, monkeypatch):
    monkeypatch.setenv("MEETING_ASSISTANT_DATA_DIR", str(tmp_path))
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind((DEFAULT_HOST, 0))
    listener.listen()
    port = listener.getsockname()[1]
    existing = ServerCredentials(port=port, token="live-server-access-value")
    write_credentials(existing)
    try:
        with pytest.raises(RuntimeError, match="already in use"):
            run_server(port, open_browser=False)
        assert read_credentials(port) == existing
    finally:
        listener.close()
        clear_credentials(existing)


def test_reserved_port_restarts_after_server_side_connection_close():
    first = _reserve_port(0)
    port = first.getsockname()[1]
    client = socket.create_connection((DEFAULT_HOST, port))
    accepted, _ = first.accept()
    accepted.close()
    client.close()
    first.close()

    restarted = _reserve_port(port)
    try:
        assert restarted.getsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR) != 0
    finally:
        restarted.close()


def test_run_server_disables_access_logging(tmp_path, monkeypatch):
    monkeypatch.setenv("MEETING_ASSISTANT_DATA_DIR", str(tmp_path))
    captured = {}

    class Config:
        def __init__(self, app, **kwargs):
            captured.update(kwargs)

    class Server:
        def __init__(self, config):
            return None

        def run(self, sockets):
            assert len(sockets) == 1

    monkeypatch.setattr("uvicorn.Config", Config)
    monkeypatch.setattr("uvicorn.Server", Server)

    run_server(0, open_browser=False, token="fixture-access-value")

    assert captured["access_log"] is False
    assert not list(tmp_path.glob("server-*.json"))
