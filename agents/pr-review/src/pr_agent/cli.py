"""CLI entry point for PR Review Agent."""

import asyncio
import sys
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .git_utils import get_repo_info, GitError
from .context import fetch_pr_data, PRFetchError
from .state import SessionManager
from .chat import ChatREPL

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def main():
    """PR Review Agent - AI-powered PR review assistant."""
    pass


@main.command()
@click.argument("pr_number", type=int)
def review(pr_number: int):
    """Start an interactive review session for a PR.
    
    Args:
        pr_number: The pull request number to review
    """
    # Detect repository
    try:
        repo_info = get_repo_info()
    except GitError as e:
        console.print(f"[bold red]❌ Error:[/bold red] {e}")
        sys.exit(1)
    
    # Fetch PR data
    console.print()
    console.print(f"[bold blue]🔍 Fetching PR #{pr_number}...[/bold blue]")
    
    try:
        pr_data = fetch_pr_data(pr_number, repo_info.owner, repo_info.repo)
    except PRFetchError as e:
        console.print(f"[bold red]❌ Error:[/bold red] {e}")
        sys.exit(1)
    
    # Display PR information
    console.print(f"[green]✓[/green] Loaded {pr_data.metadata.changed_files} files changed")
    console.print()
    
    # Create PR summary panel
    metadata = pr_data.metadata
    console.print(Panel(
        f"[bold]{metadata.title}[/bold]\n\n"
        f"By: [cyan]@{metadata.author.login}[/cyan]\n"
        f"State: [{'green' if metadata.state == 'OPEN' else 'yellow'}]{metadata.state}[/]\n"
        f"Files: [yellow]{metadata.changed_files}[/yellow] | "
        f"[green]+{metadata.additions}[/green] [red]-{metadata.deletions}[/red]",
        title=f"PR #{pr_number}",
        border_style="blue"
    ))
    console.print()
    
    # Show file summary
    if metadata.files:
        table = Table(title="Changed Files", show_header=True)
        table.add_column("File", style="cyan")
        table.add_column("Changes", justify="right", style="yellow")
        
        for file in metadata.files[:10]:  # Show first 10 files
            table.add_row(file.path, f"+{file.additions} -{file.deletions}")
        
        if len(metadata.files) > 10:
            table.add_row("...", f"and {len(metadata.files) - 10} more files")
        
        console.print(table)
        console.print()
    
    # Create and save session
    console.print("[dim]Creating session...[/dim]")
    session_manager = SessionManager()
    session = session_manager.create_session(repo_info.owner, repo_info.repo, pr_data)
    
    console.print(f"[green]✓[/green] Session saved to: [dim]{session.session_dir}[/dim]")
    console.print()
    
    # Start interactive chat
    console.print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    console.print()
    
    try:
        repl = ChatREPL(session, repo_info.root)
        asyncio.run(repl.start())
    except KeyboardInterrupt:
        console.print("\n[yellow]Session interrupted[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
