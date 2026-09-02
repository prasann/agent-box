import stat

from meeting_assistant.server_state import (
    ServerCredentials,
    clear_credentials,
    credentials_path,
    read_credentials,
    write_credentials,
)


def test_server_credentials_are_private_and_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("MEETING_ASSISTANT_DATA_DIR", str(tmp_path))
    credentials = ServerCredentials(port=8765, token="fixture-access-value")

    write_credentials(credentials)

    path = credentials_path(8765)
    assert stat.S_IMODE(tmp_path.stat().st_mode) == 0o700
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert read_credentials(8765) == credentials

    clear_credentials(credentials)
    assert not path.exists()
