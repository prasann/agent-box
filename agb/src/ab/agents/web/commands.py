"""CLI command for the Mission Control server."""

import click


@click.command(name="serve")
@click.option("--port", type=click.IntRange(1, 65535), default=4747, show_default=True)
@click.option("--reload", is_flag=True, help="Reload the API when Python files change.")
def serve(port: int, reload: bool) -> None:
    """Start Prasanna's Control Center on this Mac only."""
    import uvicorn

    click.echo(f"🚀 Prasanna's Control Center: http://127.0.0.1:{port}")
    uvicorn.run(
        "ab.agents.web.app:app",
        host="127.0.0.1",
        port=port,
        reload=reload,
    )
