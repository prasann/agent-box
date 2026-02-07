"""Find That Tab CLI - Semantic browser history search."""
import click
from rich.console import Console
from rich.table import Table
from pathlib import Path
from .models import Settings
from .database import IndexDatabase
from .indexer import HistoryIndexer
from .searcher import HistorySearcher


console = Console()


@click.group()
def cli():
    """Find That Tab - Semantic browser history search.
    
    Search your browser history by meaning, not just exact URLs.
    """
    pass


@cli.command()
@click.option('--hours', default=1, help='Hours of history to index')
def index(hours):
    """Index recent browser history.
    
    Example:
        findtab index --hours=24
    """
    settings = Settings()
    index_path = Path(settings.index_path).expanduser()
    
    # Setup database
    db = IndexDatabase(index_path)
    db.initialize()
    
    # Run indexer
    indexer = HistoryIndexer(db, settings)
    
    console.print(f"📚 Indexing last {hours} hour(s) of browser history...", style="bold blue")
    
    try:
        count = indexer.run_incremental_index(hours_back=hours)
        console.print(f"✅ Indexed {count} new entries", style="bold green")
    except Exception as e:
        console.print(f"❌ Error: {e}", style="bold red")
        raise


@cli.command()
@click.argument('query')
@click.option('--limit', default=10, help='Maximum number of results')
@click.option('--open', 'open_url', is_flag=True, help='Open first result in browser')
def search(query, limit, open_url):
    """Search browser history by intent.
    
    Examples:
        findtab search "article about MCP"
        findtab search "python documentation" --limit=20
        findtab search "github repo I visited yesterday" --open
    """
    settings = Settings()
    index_path = Path(settings.index_path).expanduser()
    
    if not index_path.exists():
        console.print("❌ No index found. Run 'findtab index' first.", style="bold red")
        return
    
    searcher = HistorySearcher(index_path)
    
    console.print(f"🔍 Searching for: [cyan]{query}[/cyan]")
    
    results = searcher.search(query, limit=limit)
    
    if not results:
        console.print("No results found. Try a different query or index more history.", style="yellow")
        return
    
    # Display results in a table
    table = Table(title=f"Found {len(results)} results", show_lines=False)
    table.add_column("#", style="cyan", width=3, justify="right")
    table.add_column("Title", style="green", no_wrap=False, max_width=50)
    table.add_column("URL", style="blue", no_wrap=False, max_width=60)
    table.add_column("When", style="yellow", width=10)
    
    for i, result in enumerate(results, 1):
        time_ago = result.time_ago()
        title = result.title[:80] + "..." if len(result.title) > 80 else result.title
        url = result.url[:100] + "..." if len(result.url) > 100 else result.url
        
        table.add_row(
            str(i),
            title,
            url,
            time_ago,
        )
    
    console.print(table)
    
    # Show summary if available
    if results[0].summary:
        console.print(f"\n📝 {results[0].summary}", style="italic dim")
    
    # Open first result if requested
    if open_url and results:
        import subprocess
        subprocess.run(['open', results[0].url])
        console.print(f"\n🌐 Opened: {results[0].url}", style="bold green")


@cli.command()
def status():
    """Show index statistics and information."""
    settings = Settings()
    index_path = Path(settings.index_path).expanduser()
    
    if not index_path.exists():
        console.print("❌ No index found. Run 'findtab index' first.", style="bold red")
        return
    
    db = IndexDatabase(index_path)
    stats = db.get_stats()
    
    console.print("\n📊 [bold blue]Index Statistics[/bold blue]\n")
    console.print(f"  Total entries: [cyan]{stats['total']:,}[/cyan]")
    
    if stats['oldest']:
        console.print(f"  Oldest entry:  [dim]{stats['oldest']}[/dim]")
    if stats['newest']:
        console.print(f"  Newest entry:  [dim]{stats['newest']}[/dim]")
    
    if stats['browsers']:
        browsers_str = ", ".join(stats['browsers'])
        console.print(f"  Browsers:      [green]{browsers_str}[/green]")
    
    console.print(f"  Index location: [dim]{index_path}[/dim]\n")


if __name__ == '__main__':
    cli()
