"""Find That Tab CLI - Semantic browser history search."""
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path
from ...core.ollama_client import OllamaClient
from ...core.config import get_settings
from .database import IndexDatabase
from .indexer import HistoryIndexer
from .search import HistorySearcher


console = Console()


@click.group(name="findtab")
def findtab_group():
    """Find That Tab - Semantic browser history search.
    
    Search your browser history by meaning, not just exact URLs.
    """
    pass


@findtab_group.command()
@click.option('--hours', default=1, help='Hours of history to index')
def index(hours):
    """Index recent browser history.
    
    Example:
        findtab index --hours=24
    """
    settings = get_settings()
    index_path = Path(settings.findtab_index_path).expanduser()
    
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


@findtab_group.command()
@click.argument('query')
@click.option('--limit', default=10, help='Maximum number of results')
@click.option('--open', 'open_url', is_flag=True, help='Open first result in browser')
def search(query, limit, open_url):
    """Search browser history semantically.
    
    Examples:
        findtab search "article about MCP"
        findtab search "python documentation" --limit=20
        findtab search "github repo I visited yesterday" --open
    """
    settings = get_settings()
    index_path = Path(settings.findtab_index_path).expanduser()
    
    if not index_path.exists():
        console.print("❌ No index found. Run 'findtab index' first.", style="bold red")
        return
    
    db = IndexDatabase(index_path)
    ollama = OllamaClient(model=settings.ollama_model, base_url=settings.ollama_url)
    
    # Check Ollama availability
    if not ollama.is_available():
        console.print("\n❌ Ollama is not running. Start with: ollama serve", style="bold red")
        return
    
    if not ollama.has_model(settings.ollama_model):
        console.print(f"\n❌ Model '{settings.ollama_model}' not found.", style="bold red")
        console.print(f"   Run: ollama pull {settings.ollama_model}")
        return
    
    searcher = HistorySearcher(db, ollama)
    console.print(f"🧠 Searching: [cyan]{query}[/cyan]")
    
    results, intent = searcher.search(query, limit=limit)
    
    if intent != query:
        console.print(f"💡 Intent: [dim]{intent}[/dim]")
    
    if not results:
        console.print("\nNo results found.", style="yellow")
        console.print("💡 Try: [cyan]agb findtab embed --batch=100[/cyan] to index more entries")
        return
    
    # Display results
    table = Table(title=f"Found {len(results)} results", show_lines=False)
    table.add_column("#", style="cyan", width=3, justify="right")
    table.add_column("Title", style="green", no_wrap=False, max_width=50)
    table.add_column("URL", style="blue", no_wrap=False, max_width=50)
    table.add_column("When", style="yellow", width=10)
    table.add_column("Score", style="magenta", width=6)
    
    for i, result in enumerate(results, 1):
        title = result.title[:80] + "..." if len(result.title) > 80 else result.title
        url = result.url[:80] + "..." if len(result.url) > 80 else result.url
        
        table.add_row(
            str(i),
            title,
            url,
            result.time_ago(),
            f"{result.relevance_score:.2f}"
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


@findtab_group.command()
def status():
    """Show index statistics and information."""
    settings = get_settings()
    index_path = Path(settings.findtab_index_path).expanduser()
    
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
    
    # Show embeddings stats
    embeddings = stats.get('embeddings', 0)
    if embeddings > 0:
        pct = (embeddings / stats['total'] * 100) if stats['total'] > 0 else 0
        console.print(f"  Embeddings:    [magenta]{embeddings:,} ({pct:.1f}%)[/magenta]")
        console.print(f"  Semantic:      [green]✓ Available[/green]")
    else:
        console.print(f"  Embeddings:    [yellow]None - run 'findtab embed'[/yellow]")
        console.print(f"  Semantic:      [dim]Not available[/dim]")
    
    console.print(f"  Index location: [dim]{index_path}[/dim]\n")


@findtab_group.command()
@click.option('--batch', default=100, help='Number of entries to process')
@click.option('--all', 'process_all', is_flag=True, help='Process all entries')
def embed(batch, process_all):
    """Generate embeddings for semantic search.
    
    Examples:
        findtab embed              # Process 100 entries
        findtab embed --batch=500  # Process 500 entries
        findtab embed --all        # Process everything
    """
    settings = get_settings()
    index_path = Path(settings.findtab_index_path).expanduser()
    
    if not index_path.exists():
        console.print("❌ No index found. Run 'findtab index' first.", style="bold red")
        return
    
    # Setup
    db = IndexDatabase(index_path)
    ollama = OllamaClient(model=settings.ollama_model, base_url=settings.ollama_url)
    
    # Check Ollama
    if not ollama.is_available():
        console.print("\n❌ Ollama is not running.", style="bold red")
        console.print("   Start with: ollama serve")
        return
    
    if not ollama.has_model("nomic-embed-text"):
        console.print("\n❌ Embedding model not found.", style="bold red")
        console.print("   Run: ollama pull nomic-embed-text")
        return
    
    searcher = HistorySearcher(db, ollama)
    stats = db.get_stats()
    
    remaining = stats['total'] - stats.get('embeddings', 0)
    if remaining == 0:
        console.print("✅ All entries already have embeddings!", style="bold green")
        return
    
    console.print(f"\n🧠 Generating embeddings...")
    console.print(f"   Remaining: {remaining:,} entries\n")
    
    if process_all:
        batch = remaining
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task(f"Processing {min(batch, remaining)} entries...", total=None)
        count = searcher.generate_embeddings(batch_size=batch)
        progress.update(task, completed=True)
    
    console.print(f"\n✅ Generated {count} embeddings", style="bold green")
    console.print(f"💡 Search with: [cyan]agb findtab search \"your query\"[/cyan]\n")


if __name__ == '__main__':
    cli()
