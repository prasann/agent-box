"""Find That Tab CLI - LLM-enriched bookmark search."""
import click
import subprocess
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from datetime import datetime
from ...core.github_models import GitHubModelsClient
from ...core.config import get_settings
from .database import BookmarkDatabase
from .indexer import BookmarkIndexer
from .search import BookmarkSearcher


console = Console()


def _get_db() -> tuple[BookmarkDatabase, bool]:
    """Get database instance and check if it exists.
    
    Returns:
        Tuple of (database, exists)
    """
    settings = get_settings()
    db = BookmarkDatabase(settings.findtab_db_path)
    exists = db.db_path.exists()
    return db, exists


@click.group(name="findtab")
def findtab_group():
    """Find That Tab - LLM-curated bookmark search.
    
    Intelligently saves and searches content worth revisiting.
    Uses LLM to classify and enrich bookmarks.
    """
    pass


@findtab_group.command()
@click.option('--force', is_flag=True, help='Force full reindex (ignores watermark)')
@click.option('--hours', type=int, default=None, help='Hours of history to process (overrides watermark)')
@click.option('--dry-run', is_flag=True, help='Show what would be indexed without saving')
def index(force, hours, dry_run):
    """Index browser history incrementally.
    
    Processes new history since last run. On first run, 
    indexes last 7 days.
    
    Examples:
        findtab index             # Incremental index
        findtab index --hours=5   # Process last 5 hours
        findtab index --force     # Reindex (ignore watermark)
        findtab index --dry-run   # Preview without saving
    """
    settings = get_settings()
    db, _ = _get_db()
    
    # Use GitHub Models API
    llm_client = GitHubModelsClient()
    if not llm_client.is_available():
        console.print("❌ GitHub CLI not authenticated.", style="bold red")
        console.print("   Run: gh auth login")
        return
    
    # Determine processing window
    from datetime import timedelta
    window_end = datetime.now()
    
    if hours:
        # Explicit hours override
        window_start = window_end - timedelta(hours=hours)
        force = True  # Treat as force when hours specified
    elif force:
        window_start = window_end - timedelta(days=settings.findtab_bootstrap_days)
    else:
        window_start = db.get_processing_window(bootstrap_days=settings.findtab_bootstrap_days)
    
    console.print("📚 [bold blue]FindTab Indexer[/bold blue]\n")
    console.print(f"  LLM:    [green]GitHub Models ({llm_client.model})[/green]")
    console.print(f"  Window: [dim]{window_start.strftime('%Y-%m-%d %H:%M')} → {window_end.strftime('%Y-%m-%d %H:%M')}[/dim]")
    
    if hours:
        console.print(f"  Mode:   [yellow]Last {hours} hours[/yellow]")
    elif force:
        console.print("  Mode:   [yellow]Force full reindex[/yellow]")
    if dry_run:
        console.print("  Mode:   [yellow]Dry run (no changes)[/yellow]")
    
    console.print()
    
    if dry_run:
        console.print("🔍 Dry run - would process history in this window")
        console.print("   Run without --dry-run to actually index")
        return
    
    # Run indexer
    indexer = BookmarkIndexer(db, settings, llm_client)
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("Extracting browser history...", total=None)
        
        try:
            stats = indexer.run_incremental_index(force_full=force, hours_back=hours)
        except Exception as e:
            progress.stop()
            console.print(f"❌ Error: {e}", style="bold red")
            raise
    
    console.print()
    console.print(f"  📥 Extracted:  [cyan]{stats.extracted}[/cyan] URLs")
    console.print(f"  🔄 Already in index: [dim]{stats.already_indexed}[/dim]")
    console.print(f"  🔎 Pre-filter: [green]{stats.prefilter_saved}[/green] save / [dim]{stats.prefilter_skipped}[/dim] skip / [yellow]{stats.prefilter_unknown}[/yellow] → LLM")
    console.print(f"  🤖 LLM:       [green]{stats.classified_save}[/green] save / [dim]{stats.classified_skip}[/dim] skip")
    console.print(f"  ✨ Enriched:   [magenta]{stats.enriched}[/magenta]")
    
    if stats.failed > 0:
        console.print(f"  ⚠️  Failed:     [yellow]{stats.failed}[/yellow]")
    
    console.print()
    console.print(f"✅ Indexed [bold green]{stats.enriched}[/bold green] new bookmarks", style="bold")


@findtab_group.command()
@click.argument('query')
@click.option('--limit', '-n', default=10, help='Maximum number of results')
@click.option('--open', 'open_url', is_flag=True, help='Open first result in browser')
@click.option('--json', 'as_json', is_flag=True, help='Output as JSON')
@click.option('--no-llm', is_flag=True, help='Skip LLM expansion/re-ranking, use FTS5 only')
def search(query, limit, open_url, as_json, no_llm):
    """Search bookmarks using natural language.
    
    Uses LLM to expand queries and re-rank results for better
    semantic search. Falls back to FTS5 when LLM is unavailable.
    
    Examples:
        findtab search "rust error handling"
        findtab search "python docs" --limit=20
        findtab search "that github repo" --open
        findtab search "react hooks" --no-llm
    """
    db, exists = _get_db()
    
    if not exists:
        console.print("❌ No bookmarks found. Run 'findtab index' first.", style="bold red")
        return
    
    llm_client = None
    if not no_llm:
        client = GitHubModelsClient()
        if client.is_available():
            llm_client = client
    
    searcher = BookmarkSearcher(db, llm_client=llm_client)
    results = searcher.search(query, limit=limit)
    
    if as_json:
        import json
        output = [
            {
                'url': r.url,
                'title': r.title,
                'category': r.category,
                'summary': r.summary,
                'topics': r.topics,
                'why_useful': r.why_useful,
            }
            for r in results
        ]
        console.print(json.dumps(output, indent=2))
        return
    
    console.print(f"🔍 Searching: [cyan]{query}[/cyan]\n")
    
    if not results:
        console.print("No results found.", style="yellow")
        console.print("💡 Try different keywords or run 'findtab index' to add more bookmarks")
        return
    
    # Display results
    console.print(f"Found [bold]{len(results)}[/bold] bookmarks:\n")
    
    for i, result in enumerate(results, 1):
        # Title and category
        emoji = result.category_emoji
        title = result.title[:70] + "..." if len(result.title) > 70 else result.title
        console.print(f"[bold cyan]{i}.[/bold cyan] {emoji} [bold]{title}[/bold]")
        
        # Summary if available
        if result.summary:
            console.print(f"   [dim]{result.summary}[/dim]")
        
        # Topics
        if result.topics:
            topics_str = ", ".join(result.topics[:4])
            console.print(f"   [magenta]Topics:[/magenta] {topics_str}")
        
        # URL and time
        console.print(f"   [cyan]{result.url}[/cyan] • [yellow]{result.time_ago()}[/yellow]")
        console.print()
    
    # Interactive selection
    if open_url and results:
        subprocess.run(['open', results[0].url])
        console.print(f"🌐 Opened: {results[0].url}", style="bold green")


@findtab_group.command()
def status():
    """Show index statistics and information."""
    db, exists = _get_db()
    
    if not exists:
        console.print("❌ No index found. Run 'findtab index' first.", style="bold red")
        return
    
    stats = db.get_stats()
    
    console.print("\n📊 [bold blue]FindTab Status[/bold blue]\n")
    
    # Last processed
    if stats['last_processed_at']:
        last = datetime.fromisoformat(stats['last_processed_at'])
        delta = datetime.now() - last
        hours_ago = int(delta.total_seconds() / 3600)
        console.print(f"  Last indexed:  [cyan]{last.strftime('%Y-%m-%d %H:%M')}[/cyan] ({hours_ago}h ago)")
    else:
        console.print("  Last indexed:  [yellow]Never[/yellow]")
    
    console.print()
    
    # Bookmark counts
    console.print(f"  📚 Total:      [bold]{stats['total']:,}[/bold] bookmarks")
    console.print(f"     Enriched:   [green]{stats['enriched']:,}[/green]")
    console.print(f"     Pending:    [yellow]{stats['pending']:,}[/yellow]")
    if stats['failed'] > 0:
        console.print(f"     Failed:     [red]{stats['failed']}[/red]")
    
    # Categories
    if stats['categories']:
        console.print()
        console.print("  📁 Categories:")
        emojis = {'docs': '📚', 'article': '📝', 'discussion': '💬', 'code': '💻', 'reference': '📖'}
        for cat, count in sorted(stats['categories'].items(), key=lambda x: -x[1]):
            emoji = emojis.get(cat, '📄')
            pct = (count / stats['enriched'] * 100) if stats['enriched'] > 0 else 0
            console.print(f"     {emoji} {cat}: [cyan]{count}[/cyan] ({pct:.0f}%)")
    
    # Date range
    if stats['oldest'] and stats['newest']:
        console.print()
        console.print(f"  📅 Date range: {stats['oldest'][:10]} → {stats['newest'][:10]}")
    
    # Browsers
    if stats['browsers']:
        browsers_str = ", ".join(stats['browsers'])
        console.print(f"  🌐 Browsers:   {browsers_str}")
    
    console.print(f"\n  📍 Database:   [dim]{stats['db_path']}[/dim]\n")


@findtab_group.command(name="list")
@click.option('--recent', '-r', default=10, help='Number of recent bookmarks to show')
@click.option('--category', '-c', help='Filter by category (docs, article, discussion, code, reference)')
def list_bookmarks(recent, category):
    """List bookmarks.
    
    Examples:
        findtab list              # Recent 10 bookmarks
        findtab list -r 20        # Recent 20 bookmarks
        findtab list -c article   # Only articles
    """
    db, exists = _get_db()
    
    if not exists:
        console.print("❌ No bookmarks found. Run 'findtab index' first.", style="bold red")
        return
    
    searcher = BookmarkSearcher(db)
    
    if category:
        results = searcher.list_by_category(category, limit=recent)
        console.print(f"📁 [bold blue]{category.title()} Bookmarks[/bold blue]\n")
    else:
        results = searcher.list_recent(limit=recent)
        console.print("📚 [bold blue]Recent Bookmarks[/bold blue]\n")
    
    if not results:
        console.print("No bookmarks found.", style="yellow")
        return
    
    for i, result in enumerate(results, 1):
        emoji = result.category_emoji
        title = result.title[:60] + "..." if len(result.title) > 60 else result.title
        console.print(f"[dim]{i:2}.[/dim] {emoji} [bold]{title}[/bold] [dim]({result.time_ago()})[/dim]")
        if result.summary:
            summary = result.summary[:80] + "..." if len(result.summary) > 80 else result.summary
            console.print(f"    [dim]{summary}[/dim]")
    
    console.print()


@findtab_group.command()
@click.option('--batch', default=50, help='Number of entries to process')
def enrich(batch):
    """Enrich pending bookmarks that failed initial processing.
    
    Use this to retry enrichment for bookmarks that were 
    classified as worth saving but failed LLM enrichment.
    
    Examples:
        findtab enrich            # Process 50 pending
        findtab enrich --batch=100
    """
    settings = get_settings()
    db, exists = _get_db()
    
    if not exists:
        console.print("❌ No index found. Run 'findtab index' first.", style="bold red")
        return
    
    stats = db.get_stats()
    pending = stats.get('pending', 0)
    
    if pending == 0:
        console.print("✅ No pending bookmarks to enrich!", style="bold green")
        return
    
    console.print(f"🔄 Enriching {min(batch, pending)} pending bookmarks...\n")
    
    llm_client = GitHubModelsClient()
    if not llm_client.is_available():
        console.print("❌ GitHub CLI not authenticated.", style="bold red")
        return
    
    indexer = BookmarkIndexer(db, settings, llm_client)
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("Enriching...", total=None)
        count = indexer.enrich_pending(limit=batch)
    
    console.print(f"\n✅ Enriched [bold green]{count}[/bold green] bookmarks")


if __name__ == '__main__':
    findtab_group()
