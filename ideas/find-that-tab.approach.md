# Find That Tab - Technical Approach

## Overview
Semantic search for browser history that finds pages by intent and meaning, not exact URLs or titles. Uses local embeddings and Ollama for natural language queries.

## The Problem

Traditional browser history search is broken:
- **Cmd+H in browser**: Only searches exact URL/title text
- **Bookmarks**: Requires manual organization
- **Brain**: "I saw that thing about MCP vs A2A... where was it?"

You remember the **meaning**, not the URL.

## User Flow

1. Run terminal command: `findtab "blog about MCP and VSCode"`
2. Agent searches local index by **intent**
3. Shows top matching pages with titles, URLs, timestamps
4. Open selected page in browser

**Use Cases**:
- "That article explaining A2A vs MCP"
- "The post with a diagram about agent orchestration"
- "Blog about Ollama function calling I read last week"
- "Documentation page for pydantic settings"

**Frequency**: 2-5 times per day

## Architecture

```
┌─────────────────────────────────┐
│  Browser History DB (SQLite)    │
│  ~/Library/Application Support/ │
│  Chrome/Safari/Firefox          │
└────────────┬────────────────────┘
             │ (read-only)
             ▼
      ┌─────────────┐
      │  Indexer    │
      │  (periodic) │
      └──────┬──────┘
             │
             ├──────────────┐
             │              │
             ▼              ▼
      ┌──────────┐   ┌──────────┐
      │  Ollama  │   │ Embedder │
      │  (3b)    │   │ (local)  │
      └────┬─────┘   └────┬─────┘
           │              │
           └──────┬───────┘
                  │
                  ▼
         ┌────────────────┐
         │  Local Index   │
         │  ~/.findtab/   │
         │  (SQLite +     │
         │   embeddings)  │
         └────────┬───────┘
                  │
                  ▼
           ┌─────────────┐
           │  CLI Query  │
           │  (findtab)  │
           └─────────────┘
```

## Key Insight: Rolling Index ✅

**Don't index everything at once.** That's slow and unnecessary.

Instead:
1. **Periodic slicing**: Every hour/day, take new history entries
2. **Lightweight extraction**: Title, URL, timestamp, maybe summary
3. **Store locally**: Tiny index that grows over time
4. **Query efficiently**: Search only what's indexed

**Benefit**: 
- Agent feels instant
- Answers improve over time
- Sustainable (not resource-heavy)
- Index once, query many times

## Implementation Strategy

### Phase 1: Simple Text Search (MVP)
Start without embeddings, just smart text matching.

**Index Structure**:
```json
{
  "entries": [
    {
      "id": "uuid",
      "url": "https://...",
      "title": "Building with MCP",
      "visit_time": "2026-02-05T14:22:00Z",
      "visit_count": 3,
      "keywords": ["mcp", "building", "vscode", "agents"],
      "summary": "Article discussing Model Context Protocol...",
    }
  ]
}
```

**Search Strategy**:
1. Extract keywords from query (using Ollama)
2. Match against: title + URL + keywords + summary
3. Rank by relevance + recency

This gets you 80% there without embeddings.

### Phase 2: Semantic Search (Enhanced)
Add embeddings for true semantic search.

**Embedding Strategy**:
- Use small local model: `nomic-embed-text` (via Ollama)
- Embed: `title + summary` (not full page content)
- Store in lightweight vector DB or just cosine similarity

## Browser History Extraction

### Chrome (Most Common)

**Location**: `~/Library/Application Support/Google/Chrome/Default/History`

**Format**: SQLite database

**Schema**:
```sql
-- urls table
CREATE TABLE urls (
  id INTEGER PRIMARY KEY,
  url TEXT,
  title TEXT,
  visit_count INTEGER,
  typed_count INTEGER,
  last_visit_time INTEGER,  -- Chrome timestamp format
  hidden INTEGER
);

-- visits table
CREATE TABLE visits (
  id INTEGER PRIMARY KEY,
  url INTEGER,  -- foreign key to urls.id
  visit_time INTEGER,
  transition INTEGER
);
```

**Extraction**:
```python
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime, timedelta

def extract_chrome_history(hours_back: int = 24) -> list[HistoryEntry]:
    """Extract recent Chrome history."""
    
    # Chrome's history DB is locked, copy first
    history_db = Path.home() / "Library/Application Support/Google/Chrome/Default/History"
    temp_db = Path("/tmp/chrome_history_copy.db")
    shutil.copy(history_db, temp_db)
    
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    
    # Chrome uses WebKit timestamp (microseconds since 1601-01-01)
    # Convert to Unix timestamp
    cutoff_time = datetime.now() - timedelta(hours=hours_back)
    chrome_cutoff = to_chrome_timestamp(cutoff_time)
    
    query = """
        SELECT urls.url, urls.title, visits.visit_time, urls.visit_count
        FROM urls
        JOIN visits ON urls.id = visits.url
        WHERE visits.visit_time > ?
        ORDER BY visits.visit_time DESC
    """
    
    cursor.execute(query, (chrome_cutoff,))
    
    entries = []
    for url, title, visit_time, visit_count in cursor.fetchall():
        entries.append(HistoryEntry(
            url=url,
            title=title or "Untitled",
            visit_time=from_chrome_timestamp(visit_time),
            visit_count=visit_count,
        ))
    
    conn.close()
    temp_db.unlink()
    
    return entries

def to_chrome_timestamp(dt: datetime) -> int:
    """Convert datetime to Chrome timestamp."""
    epoch = datetime(1601, 1, 1)
    delta = dt - epoch
    return int(delta.total_seconds() * 1_000_000)

def from_chrome_timestamp(chrome_ts: int) -> datetime:
    """Convert Chrome timestamp to datetime."""
    epoch = datetime(1601, 1, 1)
    return epoch + timedelta(microseconds=chrome_ts)
```

### Safari

**Location**: `~/Library/Safari/History.db`

**Schema**: Similar structure, different timestamp format

### Firefox

**Location**: `~/Library/Application Support/Firefox/Profiles/<profile>/places.sqlite`

**Schema**: Different table names (`moz_places`, `moz_historyvisits`)

### Multi-Browser Support

```python
class BrowserHistoryExtractor:
    """Extract history from any browser."""
    
    def detect_browsers(self) -> list[str]:
        """Detect installed browsers."""
        browsers = []
        
        chrome_path = Path.home() / "Library/Application Support/Google/Chrome"
        safari_path = Path.home() / "Library/Safari/History.db"
        firefox_path = Path.home() / "Library/Application Support/Firefox/Profiles"
        
        if chrome_path.exists():
            browsers.append("chrome")
        if safari_path.exists():
            browsers.append("safari")
        if firefox_path.exists():
            browsers.append("firefox")
        
        return browsers
    
    def extract(self, browser: str, hours_back: int = 24) -> list[HistoryEntry]:
        """Extract history from specified browser."""
        extractors = {
            "chrome": self._extract_chrome,
            "safari": self._extract_safari,
            "firefox": self._extract_firefox,
        }
        
        return extractors[browser](hours_back)
```

## Content Summarization

For each page, generate a lightweight summary to improve search.

### Strategy 1: Title + URL Analysis (Fast)

```python
def extract_keywords_from_metadata(entry: HistoryEntry) -> list[str]:
    """Extract keywords from title and URL."""
    
    # Parse URL for meaningful terms
    from urllib.parse import urlparse
    parsed = urlparse(entry.url)
    
    # Extract from path and domain
    path_parts = parsed.path.split('/')
    domain_parts = parsed.netloc.split('.')
    
    # Extract from title
    title_words = entry.title.lower().split()
    
    # Common stop words
    stop_words = {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'and'}
    
    keywords = []
    for word in title_words + path_parts + domain_parts:
        word = word.strip('/-_').lower()
        if word and word not in stop_words and len(word) > 2:
            keywords.append(word)
    
    return list(set(keywords))  # Deduplicate
```

### Strategy 2: LLM Summary (Slow but Better)

```python
def generate_summary_with_llm(entry: HistoryEntry) -> str:
    """Generate concise summary using Ollama."""
    
    prompt = f"""Given this webpage metadata, write a 1-sentence summary of what this page is about:

Title: {entry.title}
URL: {entry.url}

Focus on the topic and purpose. Be concise.

Summary:"""
    
    summary = ollama.generate(
        prompt=prompt,
        temperature=0.3,
        max_tokens=50,
    )
    
    return summary.strip()
```

### Strategy 3: Hybrid (Recommended)

```python
def enrich_entry(entry: HistoryEntry) -> EnrichedEntry:
    """Enrich history entry with metadata."""
    
    # Always extract keywords (fast)
    keywords = extract_keywords_from_metadata(entry)
    
    # Only summarize "important" pages
    should_summarize = (
        entry.visit_count > 1 or  # Visited multiple times
        is_content_site(entry.url) or  # Known content sites
        len(entry.title) > 50  # Long title = substantial content
    )
    
    summary = None
    if should_summarize:
        summary = generate_summary_with_llm(entry)
    
    return EnrichedEntry(
        **entry.dict(),
        keywords=keywords,
        summary=summary,
    )
```

## Index Management

### Local Index Structure

**SQLite database** at `~/.findtab/index.db`:

```sql
-- Main entries table
CREATE TABLE history_entries (
    id TEXT PRIMARY KEY,  -- UUID
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    visit_time TIMESTAMP NOT NULL,
    visit_count INTEGER DEFAULT 1,
    keywords TEXT,  -- JSON array
    summary TEXT,
    browser TEXT,  -- chrome, safari, firefox
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Search optimization
    search_text TEXT,  -- title + url + keywords + summary
    
    UNIQUE(url, visit_time)
);

CREATE INDEX idx_visit_time ON history_entries(visit_time DESC);
CREATE INDEX idx_search_text ON history_entries(search_text);

-- Full-text search (SQLite FTS5)
CREATE VIRTUAL TABLE history_fts USING fts5(
    url,
    title,
    keywords,
    summary,
    content=history_entries,
    content_rowid=rowid
);

-- Embeddings table (for Phase 2)
CREATE TABLE embeddings (
    entry_id TEXT PRIMARY KEY,
    embedding BLOB,  -- Serialized vector
    FOREIGN KEY(entry_id) REFERENCES history_entries(id)
);
```

### Indexer (Periodic Job)

```python
class HistoryIndexer:
    """Periodically index browser history."""
    
    def __init__(self, index_db: Path, ollama_client: OllamaClient):
        self.index_db = index_db
        self.ollama = ollama_client
        self.extractor = BrowserHistoryExtractor()
    
    def run_incremental_index(self, hours_back: int = 1):
        """Index history from last N hours."""
        
        # Detect browsers
        browsers = self.extractor.detect_browsers()
        
        all_entries = []
        for browser in browsers:
            entries = self.extractor.extract(browser, hours_back)
            all_entries.extend(entries)
        
        # Deduplicate by URL + timestamp
        unique_entries = self._deduplicate(all_entries)
        
        # Enrich with keywords and summaries
        enriched = []
        for entry in unique_entries:
            if not self._already_indexed(entry):
                enriched_entry = enrich_entry(entry)
                enriched.append(enriched_entry)
        
        # Store in index
        self._store_entries(enriched)
        
        return len(enriched)
    
    def _already_indexed(self, entry: HistoryEntry) -> bool:
        """Check if entry already in index."""
        conn = sqlite3.connect(self.index_db)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT 1 FROM history_entries WHERE url = ? AND visit_time = ?",
            (entry.url, entry.visit_time)
        )
        
        exists = cursor.fetchone() is not None
        conn.close()
        
        return exists
    
    def _store_entries(self, entries: list[EnrichedEntry]):
        """Store enriched entries in index."""
        conn = sqlite3.connect(self.index_db)
        cursor = conn.cursor()
        
        for entry in entries:
            # Prepare search text
            search_text = ' '.join(filter(None, [
                entry.title,
                entry.url,
                ' '.join(entry.keywords),
                entry.summary or '',
            ]))
            
            cursor.execute("""
                INSERT INTO history_entries 
                (id, url, title, visit_time, visit_count, keywords, summary, browser, search_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.id,
                entry.url,
                entry.title,
                entry.visit_time,
                entry.visit_count,
                json.dumps(entry.keywords),
                entry.summary,
                entry.browser,
                search_text,
            ))
        
        conn.commit()
        conn.close()
```

### Scheduling (launchd on macOS)

Create `~/Library/LaunchAgents/com.findtab.indexer.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" 
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.findtab.indexer</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/Users/USERNAME/.local/bin/findtab</string>
        <string>index</string>
        <string>--hours=1</string>
    </array>
    
    <key>StartInterval</key>
    <integer>3600</integer> <!-- Every hour -->
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>StandardOutPath</key>
    <string>/tmp/findtab-indexer.log</string>
    
    <key>StandardErrorPath</key>
    <string>/tmp/findtab-indexer-error.log</string>
</dict>
</plist>
```

Load the job:
```bash
launchctl load ~/Library/LaunchAgents/com.findtab.indexer.plist
```

## Query Engine

### Phase 1: Text-Based Search

```python
class HistorySearcher:
    """Search indexed history."""
    
    def __init__(self, index_db: Path, ollama_client: OllamaClient):
        self.index_db = index_db
        self.ollama = ollama_client
    
    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Search history by intent."""
        
        # Extract keywords from query using LLM
        keywords = self._extract_query_keywords(query)
        
        # Search using SQLite FTS5
        conn = sqlite3.connect(self.index_db)
        cursor = conn.cursor()
        
        # Build FTS5 query
        fts_query = ' OR '.join(keywords)
        
        cursor.execute("""
            SELECT 
                e.url, 
                e.title, 
                e.visit_time, 
                e.summary,
                e.visit_count,
                history_fts.rank
            FROM history_fts
            JOIN history_entries e ON history_fts.rowid = e.rowid
            WHERE history_fts MATCH ?
            ORDER BY history_fts.rank, e.visit_time DESC
            LIMIT ?
        """, (fts_query, limit))
        
        results = []
        for url, title, visit_time, summary, visit_count, rank in cursor.fetchall():
            results.append(SearchResult(
                url=url,
                title=title,
                visit_time=datetime.fromisoformat(visit_time),
                summary=summary,
                visit_count=visit_count,
                relevance_score=abs(rank),  # FTS5 rank is negative
            ))
        
        conn.close()
        
        return results
    
    def _extract_query_keywords(self, query: str) -> list[str]:
        """Extract search keywords from natural language query."""
        
        prompt = f"""Extract 3-5 key search terms from this query:

Query: "{query}"

Return only the keywords, separated by spaces. Focus on meaningful nouns and verbs.

Keywords:"""
        
        response = self.ollama.generate(
            prompt=prompt,
            temperature=0.1,
            max_tokens=30,
        )
        
        keywords = response.strip().split()
        return keywords
```

### Phase 2: Semantic Search (with Embeddings)

```python
class SemanticHistorySearcher(HistorySearcher):
    """Search with embeddings for true semantic matching."""
    
    def __init__(self, index_db: Path, ollama_client: OllamaClient):
        super().__init__(index_db, ollama_client)
        # Use Ollama's embedding model
        self.embed_model = "nomic-embed-text"
    
    def search_semantic(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Semantic search using embeddings."""
        
        # Generate query embedding
        query_embedding = self._generate_embedding(query)
        
        # Get all entry embeddings from DB
        conn = sqlite3.connect(self.index_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT e.id, e.url, e.title, e.visit_time, e.summary, emb.embedding
            FROM history_entries e
            JOIN embeddings emb ON e.id = emb.entry_id
        """)
        
        # Calculate cosine similarity
        results = []
        for entry_id, url, title, visit_time, summary, embedding_blob in cursor.fetchall():
            entry_embedding = pickle.loads(embedding_blob)
            similarity = cosine_similarity(query_embedding, entry_embedding)
            
            if similarity > 0.5:  # Threshold
                results.append(SearchResult(
                    url=url,
                    title=title,
                    visit_time=datetime.fromisoformat(visit_time),
                    summary=summary,
                    relevance_score=similarity,
                ))
        
        conn.close()
        
        # Sort by similarity and recency
        results.sort(key=lambda r: (r.relevance_score, r.visit_time), reverse=True)
        
        return results[:limit]
    
    def _generate_embedding(self, text: str) -> list[float]:
        """Generate embedding using Ollama."""
        
        response = requests.post(
            f"{self.ollama.base_url}/api/embeddings",
            json={
                "model": self.embed_model,
                "prompt": text,
            }
        )
        
        return response.json()["embedding"]
    
    def index_embeddings(self):
        """Generate embeddings for all indexed entries."""
        
        conn = sqlite3.connect(self.index_db)
        cursor = conn.cursor()
        
        # Get entries without embeddings
        cursor.execute("""
            SELECT e.id, e.title, e.summary
            FROM history_entries e
            LEFT JOIN embeddings emb ON e.id = emb.entry_id
            WHERE emb.entry_id IS NULL
        """)
        
        for entry_id, title, summary in cursor.fetchall():
            # Combine title and summary for embedding
            text = f"{title}. {summary or ''}"
            embedding = self._generate_embedding(text)
            
            # Store embedding
            cursor.execute(
                "INSERT INTO embeddings (entry_id, embedding) VALUES (?, ?)",
                (entry_id, pickle.dumps(embedding))
            )
        
        conn.commit()
        conn.close()
```

## Implementation: Python CLI Tool

### File Structure
```
find-that-tab/
├── pyproject.toml
├── README.md
├── .gitignore
├── src/
│   └── findtab/
│       ├── __init__.py
│       ├── __main__.py         # CLI entry point
│       ├── extractors/
│       │   ├── __init__.py
│       │   ├── chrome.py
│       │   ├── safari.py
│       │   └── firefox.py
│       ├── indexer.py          # Indexing engine
│       ├── searcher.py         # Search engine
│       ├── enricher.py         # Content enrichment
│       ├── database.py         # Index management
│       ├── ollama_client.py    # Shared
│       ├── models.py           # Pydantic models
│       └── config.py
└── tests/
    ├── test_extractor.py
    ├── test_indexer.py
    └── test_searcher.py
```

### Dependencies (pyproject.toml)

```toml
[project]
name = "find-that-tab"
version = "0.1.0"
description = "Semantic browser history search"
dependencies = [
    "requests",
    "pydantic>=2.0",
    "pydantic-settings",
    "python-dotenv",
    "rich",
    "click",
    "numpy",  # For embeddings/similarity
]

[project.scripts]
findtab = "findtab.__main__:cli"
```

### Entry Point: `__main__.py`

```python
"""CLI for Find That Tab."""
import click
from rich.console import Console
from rich.table import Table
from pathlib import Path
from .indexer import HistoryIndexer
from .searcher import HistorySearcher
from .database import IndexDatabase
from .ollama_client import OllamaClient
from .config import Settings

console = Console()

@click.group()
def cli():
    """Find That Tab - Semantic browser history search"""
    pass

@cli.command()
@click.option('--hours', default=1, help='Hours of history to index')
def index(hours):
    """Index recent browser history."""
    
    settings = Settings()
    
    # Initialize
    index_db = Path.home() / '.findtab' / 'index.db'
    index_db.parent.mkdir(exist_ok=True)
    
    # Setup database
    db = IndexDatabase(index_db)
    db.initialize()
    
    ollama = OllamaClient(
        model=settings.ollama_model,
        base_url=settings.ollama_url,
    )
    
    # Run indexer
    indexer = HistoryIndexer(index_db, ollama)
    
    console.print(f"📚 Indexing last {hours} hour(s) of browser history...", style="bold blue")
    
    try:
        count = indexer.run_incremental_index(hours_back=hours)
        console.print(f"✅ Indexed {count} new entries", style="bold green")
    except Exception as e:
        console.print(f"❌ Error: {e}", style="bold red")

@cli.command()
@click.argument('query')
@click.option('--limit', default=10, help='Max results')
@click.option('--open', 'open_url', is_flag=True, help='Open first result')
def search(query, limit, open_url):
    """Search browser history by intent."""
    
    settings = Settings()
    index_db = Path.home() / '.findtab' / 'index.db'
    
    if not index_db.exists():
        console.print("❌ No index found. Run 'findtab index' first.", style="bold red")
        return
    
    ollama = OllamaClient(
        model=settings.ollama_model,
        base_url=settings.ollama_url,
    )
    
    searcher = HistorySearcher(index_db, ollama)
    
    console.print(f"🔍 Searching for: {query}", style="bold blue")
    
    results = searcher.search(query, limit=limit)
    
    if not results:
        console.print("No results found.", style="yellow")
        return
    
    # Display results in a table
    table = Table(title=f"Found {len(results)} results")
    table.add_column("#", style="cyan", width=3)
    table.add_column("Title", style="green")
    table.add_column("URL", style="blue", overflow="fold")
    table.add_column("When", style="yellow", width=12)
    
    for i, result in enumerate(results, 1):
        time_ago = result.time_ago()
        table.add_row(
            str(i),
            result.title[:60],
            result.url[:80],
            time_ago,
        )
    
    console.print(table)
    
    # Show summary if available
    if results[0].summary:
        console.print(f"\n📝 {results[0].summary}", style="italic")
    
    # Open first result if requested
    if open_url:
        import subprocess
        subprocess.run(['open', results[0].url])
        console.print(f"\n🌐 Opened: {results[0].url}", style="bold green")

@cli.command()
def status():
    """Show index statistics."""
    
    index_db = Path.home() / '.findtab' / 'index.db'
    
    if not index_db.exists():
        console.print("❌ No index found.", style="bold red")
        return
    
    import sqlite3
    conn = sqlite3.connect(index_db)
    cursor = conn.cursor()
    
    # Get stats
    cursor.execute("SELECT COUNT(*) FROM history_entries")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT MIN(visit_time), MAX(visit_time) FROM history_entries")
    oldest, newest = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(DISTINCT browser) FROM history_entries")
    browsers = cursor.fetchone()[0]
    
    conn.close()
    
    console.print("📊 Index Statistics", style="bold blue")
    console.print(f"  Total entries: {total:,}")
    console.print(f"  Oldest entry: {oldest}")
    console.print(f"  Newest entry: {newest}")
    console.print(f"  Browsers: {browsers}")
    console.print(f"  Index location: {index_db}")

if __name__ == '__main__':
    cli()
```

## Setup Steps

1. **Install Ollama** (if not already):
   ```bash
   brew install ollama
   ollama pull llama3.2:3b
   ollama serve  # Start in background
   ```

2. **Install via pipx**:
   ```bash
   brew install pipx
   pipx ensurepath
   cd find-that-tab
   pipx install .
   ```

3. **Initial indexing** (may take a few minutes):
   ```bash
   # Index last 24 hours
   findtab index --hours=24
   
   # Check status
   findtab status
   ```

4. **Setup periodic indexing**:
   ```bash
   # Create launchd plist (as shown above)
   # Then load it:
   launchctl load ~/Library/LaunchAgents/com.findtab.indexer.plist
   ```

5. **Start searching!**:
   ```bash
   findtab search "blog about MCP and VSCode"
   ```

## Usage Examples

```bash
# Search by topic
findtab search "article about agent orchestration"

# Search by content
findtab search "post with diagram explaining MCP vs A2A"

# Search recent
findtab search "documentation page I read yesterday"

# Search and open
findtab search "ollama function calling guide" --open

# Search with more results
findtab search "python pydantic" --limit=20

# Manual indexing (after long browsing session)
findtab index --hours=6

# Check what's indexed
findtab status
```

## Advanced Features (Future)

### 1. Interactive Selection (fzf)

```bash
# Add to __main__.py
@cli.command()
@click.argument('query')
def find(query):
    """Interactive search with fzf."""
    import subprocess
    
    results = searcher.search(query, limit=50)
    
    # Format for fzf
    lines = [f"{r.title} | {r.url}" for r in results]
    
    # Pipe to fzf
    proc = subprocess.Popen(
        ['fzf', '--preview', 'echo {}'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    
    selected, _ = proc.communicate('\n'.join(lines))
    
    if selected:
        url = selected.split('|')[1].strip()
        subprocess.run(['open', url])
```

### 2. Browser Extension Integration

Build a Chrome/Firefox extension that:
- Triggers indexing on-demand
- Shows inline search results
- Syncs with local index in real-time

### 3. Smart Suggestions

```bash
# Agent suggests pages you might be looking for
findtab suggest

# Based on:
# - Time of day
# - Recent search patterns
# - Frequently revisited pages
```

### 4. Page Content Indexing

For Phase 3, actually fetch and index page content:

```python
def fetch_page_content(url: str) -> str:
    """Fetch and extract main content from page."""
    import requests
    from bs4 import BeautifulSoup
    
    # Only for specific domains (avoid infinite indexing)
    if not is_indexable_domain(url):
        return ""
    
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract main content (remove scripts, styles, nav)
        for tag in soup(['script', 'style', 'nav', 'footer']):
            tag.decompose()
        
        text = soup.get_text(separator=' ', strip=True)
        
        # Truncate to reasonable length
        return text[:5000]
    except:
        return ""
```

### 5. Cross-Device Sync

Optional: Sync index across machines (with privacy controls)

```python
# Use git-based sync (encrypted)
class IndexSync:
    def push(self):
        """Push index to private git repo (encrypted)."""
        pass
    
    def pull(self):
        """Pull index from other machines."""
        pass
```

## Performance Considerations

### Indexing Performance

- **Initial index (24 hours)**: ~1-2 minutes
  - 500 pages × 2 sec/page (with summaries) = ~15 minutes
  - **Optimization**: Batch summaries, skip noise
  
- **Incremental index (1 hour)**: ~5-10 seconds
  - 20-50 new pages typically
  
- **Storage**: ~1-2 MB per 1000 entries (with summaries)

### Search Performance

- **Text search (FTS5)**: <100ms for most queries
- **Semantic search (embeddings)**: ~500ms-1s
  - Depends on index size
  - Can optimize with approximate nearest neighbor (ANN)

### Optimization Strategies

```python
# 1. Skip common domains
SKIP_DOMAINS = [
    'google.com/search',
    'localhost',
    'chrome://',
    '127.0.0.1',
]

# 2. Prioritize content sites
CONTENT_SITES = [
    'github.com',
    'stackoverflow.com',
    'medium.com',
    'dev.to',
    'docs.',  # Any docs subdomain
]

# 3. Batch operations
def batch_summarize(entries: list[HistoryEntry]) -> list[str]:
    """Summarize multiple entries in one LLM call."""
    
    prompt = "Summarize each page in one sentence:\n\n"
    for i, entry in enumerate(entries):
        prompt += f"{i+1}. {entry.title} ({entry.url})\n"
    
    prompt += "\nRespond with numbered summaries."
    
    response = ollama.generate(prompt)
    summaries = parse_numbered_list(response)
    
    return summaries
```

## Privacy & Security

### Browser Database Access

- **Read-only**: Never modify browser databases
- **Copy first**: Always work with copies
- **No tracking**: Agent never sends data anywhere

### Data Storage

- **Local only**: All data stays on your machine
- **No cloud**: Not synced unless you explicitly enable it
- **Encryption option**: Can encrypt index at rest

### Sensitive Content Filtering

```python
# Don't index certain URLs
EXCLUDE_PATTERNS = [
    r'.*paypal\.com.*',
    r'.*bank.*',
    r'.*password.*',
    r'.*login.*',
    r'.*private.*',
]

def should_index(url: str) -> bool:
    """Determine if URL should be indexed."""
    return not any(re.match(pattern, url) for pattern in EXCLUDE_PATTERNS)
```

## Comparison to Existing Tools

| Feature | Find That Tab | Browser Search | Arc Browser | Mem.ai |
|---------|---------------|----------------|-------------|--------|
| Semantic search | Yes | No | Partial | Yes |
| Local-only | Yes | Yes | No | No |
| Multi-browser | Yes | No | N/A | Partial |
| Summaries | Yes | No | No | Yes |
| Privacy | 100% | 100% | Cloud | Cloud |
| Cost | Free | Free | Free | $8-15/mo |
| Speed (query) | <1s | Instant | ~1s | ~2-3s |

**Best for**: Privacy-conscious users who want semantic search without cloud services.

## Estimated Development Time

- Project setup: 30 minutes
- Browser extractors (Chrome, Safari, Firefox): 3 hours
- Indexing engine: 2 hours
- Search engine (text-based): 2 hours
- CLI interface: 1.5 hours
- launchd setup: 30 minutes
- Testing: 2 hours
- **Total (Phase 1)**: ~11.5 hours

**Phase 2 (Embeddings)**: Additional ~4-5 hours

## Why This Approach Works

✅ **Rolling index**: Scales sustainably, doesn't overwhelm  
✅ **Local-first**: Complete privacy, no cloud  
✅ **Multi-browser**: Works across Chrome, Safari, Firefox  
✅ **Semantic**: Find by meaning, not exact text  
✅ **Fast**: Index once, query many times  
✅ **Lightweight**: SQLite + FTS5, no heavy infrastructure  
✅ **Progressive**: Start simple (text), add embeddings later

## Limitations

- Initial indexing takes time (for 24+ hours of history)
- Only indexes visited pages (not bookmarks, tabs)
- Summaries quality depends on title/URL clarity
- Doesn't index page content (Phase 1)
- macOS only (Linux/Windows need different paths)
- Browser must be closed or DB copied (locked otherwise)

## Next Steps

After documenting, ready to implement?

1. Start with Chrome extractor (most common)
2. Build simple text-based search (no embeddings yet)
3. Add periodic indexing
4. Test with real queries
5. Add other browsers
6. Enhance with embeddings (Phase 2)
