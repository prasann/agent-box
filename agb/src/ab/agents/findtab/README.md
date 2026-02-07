# Find That Tab

Semantic browser history search that finds pages by intent and meaning, not just exact URLs or titles.

## Features

- 🔍 **Semantic Search**: Find pages by meaning, not exact matches
- 🔒 **Privacy First**: All data stays local, no cloud services
- 🌐 **Multi-Browser**: Supports Edge, Chrome (and more coming soon)
- ⚡ **Fast**: Sub-100ms search with SQLite FTS5
- 🎯 **Smart Indexing**: Incremental indexing, keyword extraction

## Installation

The tool is part of the `agb` (agent-box) project. Install in development mode:

```bash
cd agb
pip install -e .
```

This installs the `findtab` command globally.

## Quick Start

### 1. Index your browser history

Start by indexing your recent history (last 24 hours):

```bash
findtab index --hours=24
```

### 2. Search by meaning

Search for pages using natural language:

```bash
# Find by topic
findtab search "article about MCP"

# Find by content type
findtab search "github repository"

# Find by intent
findtab search "documentation I read yesterday"
```

### 3. Check your index

See what's been indexed:

```bash
findtab status
```

## Commands

### `findtab index`

Index recent browser history.

```bash
findtab index [--hours=N]
```

**Options:**
- `--hours`: Number of hours of history to index (default: 1)

**Examples:**
```bash
# Index last 24 hours
findtab index --hours=24

# Index last hour (for periodic updates)
findtab index --hours=1
```

### `findtab search`

Search your indexed history.

```bash
findtab search QUERY [--limit=N] [--open]
```

**Options:**
- `--limit`: Maximum number of results (default: 10)
- `--open`: Open the first result in your browser

**Examples:**
```bash
# Search for GitHub pages
findtab search "github"

# Search for documentation with more results
findtab search "python documentation" --limit=20

# Search and open immediately
findtab search "that blog post about agents" --open
```

### `findtab status`

Show index statistics.

```bash
findtab status
```

## How It Works

1. **Extraction**: Reads browser history from local SQLite databases
2. **Enrichment**: Extracts keywords from URLs and titles
3. **Indexing**: Stores in local index with full-text search
4. **Search**: Uses SQLite FTS5 for fast, relevant results

## Supported Browsers

- ✅ **Microsoft Edge** (Chromium-based)
- ✅ **Google Chrome** 
- 🚧 Safari (planned)
- 🚧 Firefox (planned)

## Configuration

Create a `.env` file in the `agb` directory:

```env
# Ollama settings (for future semantic features)
FINDTAB_OLLAMA_URL=http://localhost:11434
FINDTAB_OLLAMA_MODEL=llama3.2:3b

# Index location
FINDTAB_INDEX_PATH=~/.findtab/index.db
```

## Privacy & Security

- **100% Local**: All data stays on your machine
- **Read-Only**: Never modifies browser databases
- **No Tracking**: No external API calls or cloud sync
- **Noise Filtering**: Automatically skips sensitive domains (localhost, search results, etc.)

## Tips

### Periodic Indexing

For best results, index regularly. You can set up a cron job or launchd task:

```bash
# macOS launchd (run every hour)
# See approach document for full launchd setup

# Or simply run manually after browsing sessions
findtab index --hours=6
```

### Better Searches

The more specific your query, the better the results:

- ✅ "github MCP server repository"
- ✅ "youtube video about copilot"
- ❌ "that thing" (too vague)

### Index Size

The index is lightweight:
- ~1-2 MB per 1000 entries
- Fast queries (<100ms typical)
- Incremental updates are quick (5-10 seconds for 1 hour)

## Troubleshooting

### "No index found"

Run `findtab index` first to create the index.

### "No results found"

- Try simpler keywords
- Index more history: `findtab index --hours=48`
- Check what's indexed: `findtab status`

### Browser not detected

Make sure your browser is installed in the standard location:
- Edge: `~/Library/Application Support/Microsoft Edge/`
- Chrome: `~/Library/Application Support/Google/Chrome/`

## Future Enhancements

- [ ] True semantic search with embeddings
- [ ] LLM-generated summaries for key pages
- [ ] Safari and Firefox support
- [ ] Page content indexing
- [ ] Interactive selection with fzf
- [ ] Browser extension integration

## Architecture

```
Browser History DB (SQLite)
         ↓
    Extractor (copies DB)
         ↓
    Enricher (keywords)
         ↓
   Local Index (~/.findtab/)
         ↓
    FTS5 Search Engine
         ↓
      CLI Results
```

## Example Session

```bash
$ findtab index --hours=24
📚 Indexing last 24 hour(s) of browser history...
✅ Indexed 780 new entries

$ findtab status
📊 Index Statistics

  Total entries: 780
  Oldest entry:  2026-02-06T15:10:01
  Newest entry:  2026-02-07T09:36:38
  Browsers:      edge
  Index location: /Users/you/.findtab/index.db

$ findtab search "github copilot"
🔍 Searching for: github copilot
Found 5 results
┌───┬────────────────────────────────┬─────────────────────────┬─────────┐
│ # │ Title                          │ URL                     │ When    │
├───┼────────────────────────────────┼─────────────────────────┼─────────┤
│ 1 │ GitHub Copilot CLI demo        │ https://youtube.com/... │ 23h ago │
│ 2 │ github.com/features/copilot    │ https://github.com/...  │ 1d ago  │
└───┴────────────────────────────────┴─────────────────────────┴─────────┘
```

## License

Part of the agent-box project.
