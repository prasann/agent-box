"""Find That Tab CLI - Semantic browser history search."""
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path
from .models import Settings
from .database import IndexDatabase
from .indexer import HistoryIndexer
from .searcher import HistorySearcher
from .semantic import SemanticSearcher
from .ollama_client import OllamaClient


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
@click.option('--semantic', is_flag=True, help='Use semantic search (requires embeddings)')
def search(query, limit, open_url, semantic):
    """Search browser history by intent.
    
    Examples:
        findtab search "article about MCP"
        findtab search "python documentation" --limit=20
        findtab search "github repo I visited yesterday" --open
        findtab search "blog explaining AI agents" --semantic
    """
    settings = Settings()
    index_path = Path(settings.index_path).expanduser()
    
    if not index_path.exists():
        console.print("❌ No index found. Run 'findtab index' first.", style="bold red")
        return
    
    db = IndexDatabase(index_path)
    
    # Use semantic search if requested
    if semantic:
        ollama = OllamaClient(settings)
        
        # Check Ollama availability
        if not ollama.check_availability():
            console.print("\n❌ Semantic search requires Ollama with models installed.", style="bold red")
            return
        
        searcher = SemanticSearcher(db, ollama)
        console.print(f"🧠 Semantic search for: [cyan]{query}[/cyan]")
        results = searcher.search(query, limit=limit)
    else:
        # Use keyword search
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
    table.add_column("URL", style="blue", no_wrap=False, max_width=50)
    table.add_column("When", style="yellow", width=10)
    
    if semantic:
        table.add_column("Score", style="magenta", width=6)
    
    for i, result in enumerate(results, 1):
        time_ago = result.time_ago()
        title = result.title[:80] + "..." if len(result.title) > 80 else result.title
        url = result.url[:80] + "..." if len(result.url) > 80 else result.url
        
        row = [str(i), title, url, time_ago]
        if semantic:
            row.append(f"{result.relevance_score:.2f}")
        
        table.add_row(*row)
    
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


@cli.command()
@click.option('--batch', default=100, help='Number of entries to process')
@click.option('--all', 'process_all', is_flag=True, help='Process all entries')
def embed(batch, process_all):
    """Generate embeddings for semantic search.
    
    This enables true semantic search that understands meaning.
    Requires Ollama with nomic-embed-text model.
    
    Examples:
        findtab embed              # Process 100 entries
        findtab embed --batch=500  # Process 500 entries
        findtab embed --all        # Process everything
    """
    settings = Settings()
    index_path = Path(settings.index_path).expanduser()
    
    if not index_path.exists():
        console.print("❌ No index found. Run 'findtab index' first.", style="bold red")
        return
    
    # Check Ollama
    ollama = OllamaClient(settings)
    if not ollama.check_availability():
        console.print("\n❌ Embeddings require Ollama with models installed.", style="bold red")
        console.print("\nSetup instructions:")
        console.print("  1. Install Ollama: brew install ollama")
        console.print("  2. Start Ollama: ollama serve")
        console.print("  3. Pull embedding model: ollama pull nomic-embed-text")
        console.print(f"  4. Pull LLM model: ollama pull {settings.ollama_model}")
        return
    
    db = IndexDatabase(index_path)
    searcher = SemanticSearcher(db, ollama)
    
    stats = db.get_stats()
    total = stats['total']
    existing = stats.get('embeddings', 0)
    remaining = total - existing
    
    if remaining == 0:
        console.print("✅ All entries already have embeddings!", style="bold green")
        return
    
    console.print(f"\n🧠 Generating embeddings...")
    console.print(f"   Total entries: {total:,}")
    console.print(f"   Already embedded: {existing:,}")
    console.print(f"   Remaining: {remaining:,}\n")
    
    if process_all:
        batch = remaining
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Processing {min(batch, remaining)} entries...", total=None)
        
        count = searcher.generate_embeddings(batch_size=batch)
        
        progress.update(task, completed=True)
    
    console.print(f"\n✅ Generated {count} embeddings", style="bold green")
    console.print(f"💡 Now you can use: [cyan]findtab search \"query\" --semantic[/cyan]\n")


if __name__ == '__main__':
    cli()
