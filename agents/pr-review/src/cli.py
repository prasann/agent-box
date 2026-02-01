"""CLI entry point for PR Review Agent."""

import sys
import click
from rich.console import Console

console = Console()


@click.command()
@click.option('--port', default=8501, help='Port to run Streamlit on (default: 8501)')
def main(port: int):
    """PR Review Agent - AI-powered PR review with Streamlit UI.
    
    Usage: 
        cd /path/to/your-repo
        pr-agent
    
    Or create an alias in ~/.zshrc:
        alias pr-agent='cd ~/agent-box/agents/pr-review && uv run pr-agent'
    """
    import subprocess
    
    console.print(f"[green]🚀 Launching PR Review Agent on port {port}...[/green]")
    console.print()
    try:
        subprocess.run([
            "streamlit", "run", "streamlit_app.py",
            "--server.port", str(port),
            "--server.headless", "true"
        ], check=True)
    except subprocess.CalledProcessError:
        console.print("[red]❌ Failed to start Streamlit[/red]")
        console.print("[yellow]💡 Make sure streamlit is installed: uv sync[/yellow]")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Shutting down...[/yellow]")
        sys.exit(0)


if __name__ == "__main__":
    main()


