"""CLI entry point for PR Review Agent - Simplified."""

import asyncio
import sys
import click
from rich.console import Console

from .repl import ReviewREPL

console = Console()


@click.command()
@click.argument("pr_number", type=int)
@click.version_option(version="0.1.0")
def main(pr_number: int):
    """PR Review Agent - Simple AI-powered PR review.
    
    Usage: pr-agent <pr_number>
    
    Args:
        pr_number: The pull request number to review
    """
    try:
        repl = ReviewREPL(pr_number)
        asyncio.run(repl.start())
    except KeyboardInterrupt:
        console.print("\n[yellow]Session interrupted[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        sys.exit(1)

