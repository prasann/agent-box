# FindTab v2 Implementation Plan

## Overview

Rebuild FindTab as an LLM-native bookmark curator that intelligently saves and searches content worth revisiting.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Processing model | Incremental with watermark | Process only new data since last run |
| Initial bootstrap | Last 7 days | Avoid processing entire history on first run |
| Filter stage | Ollama (qwen3:1.7b) | Fast, local, cost-effective for classification |
| Enrich stage | Copilot CLI | Premium model quality for metadata extraction |
| Search | FTS5 + LLM | No embeddings, rely on LLM intelligence |
| Storage | `~/.agb/findtab/bookmarks.db` | Centralized agb data directory |

## Watermark Logic

```
┌─────────────────────────────────────────────────────────────┐
│ On each run:                                                │
│                                                             │
│ 1. Read last_processed_at from metadata table               │
│ 2. If NULL (first run): set window = now - 7 days           │
│ 3. Else: set window = last_processed_at                     │
│ 4. Extract history from window to now                       │
│ 5. Process and index                                        │
│ 6. Update last_processed_at = now                           │
└─────────────────────────────────────────────────────────────┘

Example scenarios:
- First run ever: Process last 7 days
- Daily run: Process last ~24 hours  
- After 5-day vacation: Process last 5 days (likely sparse)
- Multiple runs same day: Process only new entries since last run
```

## Database Schema

```sql
-- Metadata for tracking state
CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT
);
-- Keys: 'last_processed_at', 'schema_version'

-- Main bookmarks table
CREATE TABLE bookmarks (
    id TEXT PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    
    -- LLM-enriched fields
    category TEXT,              -- docs, article, discussion, code, reference
    summary TEXT,               -- 1-2 sentence description
    topics TEXT,                -- JSON array: ["rust", "cli", "error-handling"]
    why_useful TEXT,            -- Why someone would revisit this
    
    -- Processing metadata
    first_visit_at TIMESTAMP,   -- First time visited
    last_visit_at TIMESTAMP,    -- Most recent visit
    visit_count INTEGER DEFAULT 1,
    browser TEXT,
    
    -- Index metadata
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    enriched_at TIMESTAMP,      -- When LLM enrichment completed
    enrichment_status TEXT DEFAULT 'pending'  -- pending, enriched, failed
);

-- Full-text search index
CREATE VIRTUAL TABLE bookmarks_fts USING fts5(
    title, 
    summary, 
    topics, 
    why_useful,
    content='bookmarks',
    content_rowid='rowid'
);

-- Triggers to sync FTS
CREATE TRIGGER bookmarks_fts_insert AFTER INSERT ON bookmarks BEGIN
    INSERT INTO bookmarks_fts(rowid, title, summary, topics, why_useful)
    VALUES (new.rowid, new.title, new.summary, new.topics, new.why_useful);
END;

CREATE TRIGGER bookmarks_fts_update AFTER UPDATE ON bookmarks BEGIN
    UPDATE bookmarks_fts 
    SET title = new.title, summary = new.summary, 
        topics = new.topics, why_useful = new.why_useful
    WHERE rowid = new.rowid;
END;

CREATE TRIGGER bookmarks_fts_delete AFTER DELETE ON bookmarks BEGIN
    DELETE FROM bookmarks_fts WHERE rowid = old.rowid;
END;
```

## Directory Structure

```
~/.agb/
├── findtab/
│   └── bookmarks.db          # SQLite database
├── shell/                    # Future: shell agent data
├── text/                     # Future: text agent data
└── logs/                     # Shared logs directory
```

## Processing Pipeline

### Stage 1: Extract

```python
def extract_history(since: datetime) -> list[HistoryEntry]:
    """Extract browser history entries since given timestamp."""
    # 1. Read from Chrome/Edge SQLite databases
    # 2. Filter to entries with visit_time > since
    # 3. Dedupe by URL (keep latest visit time, sum visit counts)
    # 4. Return list of {url, title, visit_time, visit_count, browser}
```

### Stage 2: Dedupe Against Index

```python
def filter_new_urls(entries: list[HistoryEntry]) -> list[HistoryEntry]:
    """Remove entries already in bookmarks table."""
    # 1. Query existing URLs from bookmarks table
    # 2. Filter out entries where URL already exists
    # 3. For existing URLs, optionally update visit_count/last_visit_at
    # 4. Return only truly new entries
```

### Stage 3: LLM Classification (Ollama)

```python
def classify_batch(entries: list[HistoryEntry]) -> list[ClassifiedEntry]:
    """Use Ollama to classify which entries are worth saving."""
    
    prompt = """You are a bookmark curator. For each URL, decide if it's worth 
saving for future reference.

SAVE if it's:
- An article, blog post, or tutorial worth revisiting
- Documentation or reference material
- A GitHub repo, issue, or PR with useful content
- A Reddit/X.com thread with substantive discussion
- Stack Overflow question with good answers

SKIP if it's:
- Behind authentication (email, banking, shopping, dashboards)
- Ephemeral content (search results, feeds, notifications)
- Video content (YouTube, Vimeo, TikTok)
- Navigation/landing pages without substance
- Social media profiles or timelines

URLs to classify:
{formatted_entries}

Respond with JSON array:
[{{"index": 1, "save": true, "reason": "technical article"}}, ...]
"""
    
    # Batch size: ~20-50 URLs per call for efficiency
    # Parse response, return entries marked save=true
```

### Stage 4: LLM Enrichment (Copilot CLI)

```python
def enrich_batch(entries: list[ClassifiedEntry]) -> list[EnrichedEntry]:
    """Use Copilot CLI to generate rich metadata."""
    
    prompt = """For each URL below, extract bookmark metadata.

URLs:
{formatted_entries}

For each, provide:
- category: one of [docs, article, discussion, code, reference]
- summary: 1-2 sentence description of what this page contains
- topics: list of 3-5 key concepts/technologies mentioned
- why_useful: brief reason someone would want to revisit this

Respond as JSON array:
[{{"index": 1, "category": "article", "summary": "...", "topics": [...], "why_useful": "..."}}, ...]
"""
    
    # Call: echo "$prompt" | gh copilot explain -t code
    # Or use subprocess to call copilot CLI
    # Parse JSON response
```

### Stage 5: Store

```python
def store_bookmarks(entries: list[EnrichedEntry]):
    """Store enriched entries in SQLite."""
    # 1. Insert into bookmarks table
    # 2. FTS triggers handle search index automatically
    # 3. Update metadata.last_processed_at
```

## CLI Commands

### `findtab index`

Run the incremental indexing pipeline.

```bash
$ findtab index
📚 Processing browser history...
   Window: 2026-02-19 10:30:00 → 2026-02-20 14:45:00
   Found: 127 new URLs
   
🤖 Classifying with Ollama...
   Worth saving: 23 URLs
   Skipped: 104 URLs
   
✨ Enriching with Copilot...
   Enriched: 23 bookmarks
   
✅ Indexed 23 new bookmarks
   Total in index: 156 bookmarks
```

Options:
- `--dry-run`: Show what would be processed without saving
- `--force-full`: Ignore watermark, process last 7 days

### `findtab search <query>`

Search bookmarks using FTS5.

```bash
$ findtab search "rust error handling"
🔍 Searching: rust error handling

Found 3 bookmarks:

1. Error Handling in Rust - The Complete Guide
   📁 article | 🕐 2 days ago
   Summary: Comprehensive guide covering Result, Option, and the ? operator
   Topics: rust, error-handling, result-type
   https://blog.example.com/rust-error-handling

2. rust-lang/rust - Error handling RFC
   📁 discussion | 🕐 5 days ago  
   Summary: RFC discussion about improving error handling ergonomics
   Topics: rust, rfc, language-design
   https://github.com/rust-lang/rust/discussions/12345

[1-3 or Enter to cancel]: 
```

Options:
- `--limit N`: Max results (default: 10)
- `--open`: Open first result in browser
- `--json`: Output as JSON for scripting

### `findtab status`

Show index statistics.

```bash
$ findtab status
📊 FindTab Status

Index: ~/.agb/findtab/bookmarks.db
Last processed: 2026-02-20 10:30:00 (4 hours ago)

Bookmarks: 156 total
  📁 article:    67 (43%)
  📁 docs:       34 (22%)
  📁 code:       28 (18%)
  📁 discussion: 20 (13%)
  📁 reference:   7 (4%)

Browsers: chrome, edge
Date range: 2026-02-13 → 2026-02-20
```

### `findtab list`

List recent bookmarks.

```bash
$ findtab list --recent 10
Recent bookmarks:

1. [article] Building CLI Tools in Rust (2h ago)
2. [docs] SQLite FTS5 Documentation (5h ago)
3. [discussion] Reddit: Best practices for... (1d ago)
...
```

## Implementation Tasks

### Phase 1: Foundation

- [ ] **1.1 Update config module**
  - Add `AGB_DATA_DIR = ~/.agb`
  - Add `FINDTAB_DB_PATH = ~/.agb/findtab/bookmarks.db`
  - Ensure directory creation on startup

- [ ] **1.2 New database schema**
  - Create new `database.py` with schema above
  - Add metadata table for watermark tracking
  - Add migration support (or fresh start)

- [ ] **1.3 Watermark logic**
  - `get_last_processed()` → datetime or None
  - `set_last_processed(timestamp)`
  - Bootstrap logic: if None, use 7 days ago

### Phase 2: Classification

- [ ] **2.1 Batch classifier**
  - New `classifier.py` module
  - Ollama batch prompt implementation
  - JSON parsing with error handling
  - Configurable batch size (default: 30)

- [ ] **2.2 Update Ollama client**
  - Add method for batch classification
  - Handle large batches (split if needed)

### Phase 3: Enrichment

- [ ] **3.1 Copilot CLI integration**
  - New `enricher.py` module (replace existing)
  - Subprocess call to `gh copilot`
  - JSON response parsing
  - Error handling and retries

- [ ] **3.2 Batch enrichment**
  - Process in batches of 10-20
  - Handle partial failures gracefully

### Phase 4: Search

- [ ] **4.1 FTS5 search**
  - New `search.py` (replace existing)
  - Simple FTS5 MATCH query
  - Score-based ranking
  - Remove all embedding logic

- [ ] **4.2 Interactive results**
  - Display formatted results
  - Optional: number selection to open URL

### Phase 5: CLI Updates

- [ ] **5.1 Update commands.py**
  - Refactor `index` command for new pipeline
  - Refactor `search` command for FTS5
  - Update `status` command for new schema
  - Add `list` command

- [ ] **5.2 Remove deprecated code**
  - Remove `embed` command
  - Remove embedding-related code
  - Clean up old enricher

### Phase 6: Polish

- [ ] **6.1 Update README**
  - Document new architecture
  - Update examples
  - Remove embedding references

- [ ] **6.2 Testing**
  - Test incremental processing
  - Test watermark logic
  - Test classification accuracy
  - Test search quality

## Files to Modify

| File | Action | Changes |
|------|--------|---------|
| `core/config.py` | Modify | Add `~/.agb` paths |
| `findtab/models.py` | Modify | Update data models |
| `findtab/database.py` | Rewrite | New schema, watermark |
| `findtab/classifier.py` | Create | Ollama batch classification |
| `findtab/enricher.py` | Rewrite | Copilot CLI integration |
| `findtab/search.py` | Rewrite | FTS5 only, remove embeddings |
| `findtab/indexer.py` | Rewrite | New pipeline with stages |
| `findtab/commands.py` | Modify | Update CLI commands |
| `findtab/README.md` | Modify | Update documentation |

## Dependencies

Current:
- `ollama` (via requests)
- `sqlite3` (stdlib)
- `click` (CLI)
- `rich` (output formatting)
- `pydantic` (models)

New:
- `gh` CLI with Copilot extension (for enrichment)

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Copilot CLI not available | Fallback to Ollama-only enrichment |
| Ollama classification errors | Validate JSON, retry on parse failure |
| Large history gaps | Cap single-run processing to 7 days max |
| FTS5 search quality | Can add LLM re-ranking later if needed |

## Success Criteria

1. ✅ Incremental processing works correctly (watermark logic)
2. ✅ Ollama filters out auth/ephemeral content effectively
3. ✅ Copilot generates useful, accurate metadata
4. ✅ Search finds relevant bookmarks by natural language
5. ✅ Daily runs complete in < 2 minutes for typical usage
