"""Thin CLI bridge to the isolated meeting-assistant package."""

from __future__ import annotations

import json
import os

import click

DEFAULT_PORT = int(os.getenv("MEETING_ASSISTANT_PORT", "8765"))


def _meeting_cli():
    try:
        from meeting_assistant import cli
    except ModuleNotFoundError as error:
        if error.name and error.name.startswith("meeting_assistant"):
            raise click.ClickException(
                "Meeting support is not installed. From the repository run "
                "`uv sync --project agb --extra meeting`, or inject "
                "`../meeting-assistant[audio,stt]` into the pipx environment."
            ) from error
        raise
    return cli


@click.group("meeting")
def meeting_group() -> None:
    """Run the local Microsoft Teams meeting assistant."""


@meeting_group.command("start")
@click.option("--port", type=click.IntRange(1024, 65535), default=DEFAULT_PORT, show_default=True)
@click.option("--no-open", is_flag=True, help="Do not open the browser automatically.")
def start(port: int, no_open: bool) -> None:
    """Start the loopback server in the foreground."""
    click.echo(f"Meeting Assistant starting at http://127.0.0.1:{port}")
    click.echo("Press Ctrl+C to stop. Audio and transcripts remain local by default.")
    _meeting_cli().run_server(port, open_browser=not no_open)


@meeting_group.command("open")
@click.option("--port", type=click.IntRange(1024, 65535), default=DEFAULT_PORT, show_default=True)
def open_command(port: int) -> None:
    """Open the running meeting UI."""
    if not _meeting_cli().open_ui(port):
        raise click.ClickException("The default browser could not be opened.")


@meeting_group.command("status")
@click.option("--port", type=click.IntRange(1024, 65535), default=DEFAULT_PORT, show_default=True)
def status(port: int) -> None:
    """Show server and recording status."""
    try:
        value = _meeting_cli().fetch_status(port)
    except RuntimeError as error:
        raise click.ClickException(str(error)) from error
    click.echo(json.dumps(value, indent=2))
