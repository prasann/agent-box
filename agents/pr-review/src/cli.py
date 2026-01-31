"""CLI entry point for PR Review Agent."""

import sys
import subprocess
import webbrowser
import time
import click
from pathlib import Path
from rich.console import Console

console = Console()


@click.command()
@click.argument("pr_number", type=int)
@click.option("--port", default=8000, help="Port for Chainlit server")
@click.version_option(version="0.1.0")
def main(pr_number: int, port: int):
    """PR Review Agent - AI-powered PR review with Chainlit UI.
    
    Usage: pr-agent <pr_number>
    
    Args:
        pr_number: The pull request number to review
    """
    try:
        console.print("[bold blue]🚀 Starting PR Review Agent...[/bold blue]")
        console.print(f"[dim]PR Number: {pr_number}[/dim]")
        console.print(f"[dim]Port: {port}[/dim]")
        console.print()
        
        # Get app.py path
        app_dir = Path(__file__).parent.parent
        app_path = app_dir / "app.py"
        
        if not app_path.exists():
            console.print(f"[red]❌ Error: app.py not found at {app_path}[/red]")
            sys.exit(1)
        
        # Start Chainlit server
        url = f"http://localhost:{port}"
        console.print(f"[green]✓[/green] Starting server at {url}")
        console.print("[dim]Press Ctrl+C to stop[/dim]")
        console.print()
        
        # Open browser after short delay
        def open_browser():
            time.sleep(2)
            console.print(f"[green]🌐 Opening browser...[/green]")
            webbrowser.open(url)
        
        import threading
        threading.Thread(target=open_browser, daemon=True).start()
        
        # Run Chainlit (blocking)
        subprocess.run([
            "chainlit", "run", str(app_path),
            "--port", str(port),
            "--headless"
        ])
        
    except KeyboardInterrupt:
        console.print("\n[yellow]✓ Server stopped[/yellow]")
    except FileNotFoundError as e:
        if "chainlit" in str(e):
            console.print("[red]❌ Error: chainlit not found[/red]")
            console.print("[dim]Install with: uv pip install chainlit[/dim]")
        else:
            console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


