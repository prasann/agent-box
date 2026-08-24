"""CLI bridge to the repository-local Control Center application."""

import sys
from pathlib import Path

import click


def _web_app_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "web-app"


@click.command(name="serve")
@click.option("--port", type=click.IntRange(1, 65535), default=4747, show_default=True)
@click.option("--reload", is_flag=True, help="Reload the API when Python files change.")
def serve(port: int, reload: bool) -> None:
    """Start Prasanna's Control Center on this Mac only."""
    import uvicorn

    web_app_dir = _web_app_dir()
    if not (web_app_dir / "backend" / "app.py").is_file():
        raise click.ClickException(
            f"Control Center source not found at {web_app_dir}. "
            "Run this command from an editable Agent Box checkout."
        )

    sys.path.insert(0, str(web_app_dir))
    click.echo(f"🚀 Prasanna's Control Center: http://127.0.0.1:{port}")
    uvicorn.run(
        "backend.app:app",
        host="127.0.0.1",
        port=port,
        reload=reload,
        reload_dirs=[str(web_app_dir / "backend")] if reload else None,
    )
