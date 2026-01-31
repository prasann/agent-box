"""CLI entry point for PR Review Agent."""

import sys
from rich.console import Console

console = Console()


def main():
    """PR Review Agent - AI-powered PR review with Chainlit UI.
    
    Usage: 
        cd /path/to/your-repo
        cd /path/to/agent-box/agents/pr-review
        uv run python -m chainlit run app.py
    
    Or create an alias in ~/.zshrc:
        alias pr-agent='cd ~/agent-box/agents/pr-review && uv run python -m chainlit run app.py'
    """
    console.print("[yellow]Note:[/yellow] This is a placeholder CLI.")
    console.print()
    console.print("[bold]To run PR Review Agent:[/bold]")
    console.print("  1. Navigate to this project directory")
    console.print("  2. Run: [cyan]uv run python -m chainlit run app.py[/cyan]")
    console.print()
    console.print("[bold]Or create an alias:[/bold]")
    console.print("  [cyan]alias pr-agent='cd ~/agent-box/agents/pr-review && uv run python -m chainlit run app.py'[/cyan]")
    console.print()
    sys.exit(0)


