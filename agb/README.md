# AB - Personal AI Agents

Single local tool (`agb`) that provides AI agents through both CLI commands and Prasanna's Control Center, a private web dashboard.

## Features

- 🧠 **Local AI**: All processing via Ollama (private, fast, free)
- 🎯 **Simple CLI**: `agb <agent> <action>` - intuitive command structure
- 📦 **Unified Package**: Install once, get all agents
- 🔧 **Easy to Extend**: Add new agents in minutes
- 🎨 **Beautiful Output**: Rich terminal interface with colors and panels
- 🧭 **Control Center**: Run and inspect agents from a localhost-only web app

## Quick Start

### Prerequisites

1. **Install Ollama**:
   ```bash
   brew install ollama
   ollama serve
   ```

2. **Pull a model**:
   ```bash
   ollama pull llama3.2:3b
   ```

### Installation

```bash
# From the agb directory
pipx install .

# Or in development mode
pip install -e .
```

### Usage

```bash
# Text agent - fix grammar and typos
agb text fix

# Text agent - full rewrite
agb text rewrite

# Shell agent - clean up history
agb shell purge              # Preview mode (safe)
agb shell purge --no-preview # Actually modify

# Control Center - dashboard, FindTab, Text, Shell preview, and library
agb serve                    # Opens at http://127.0.0.1:4747

# Get help
agb --help
agb shell --help
```

### Prasanna's Control Center

The Control Center lives in the repository's top-level `web-app/` folder beside `xbar/`.
It imports the existing agents from `agb/src/ab/` and serves its built React application
and FastAPI backend from one localhost-only process:

```bash
agb serve
agb serve --port 4748
```

Open `http://127.0.0.1:4747` to use the dashboard. It exposes FindTab search and background indexing, paste-in/copy-out text tools, a read-only shell purge preview, health checks, recent activity, and a read-only browser for `vscode-prompts`.

`agb serve` expects an editable source checkout so it can load `web-app/backend`. The web UI intentionally cannot perform a destructive shell purge. Use the CLI after reviewing the preview. Autostart is not installed by default.

## Available Agents

### Text Agent

Fix grammar, typos, and rewrite text from your clipboard.

**Commands:**

```bash
# Fix typos and grammar (minimal changes)
agb text fix

# Full rewrite for clarity and professionalism
agb text rewrite

# Skip preview (faster)
agb text fix --no-preview
agb text rewrite --no-preview
```

**Workflow:**
1. Copy text (Cmd+C)
2. Run `agb text fix` or `agb text rewrite`
3. Paste result (Cmd+V)

**Examples:**

Original: `i have an idee for one more agent`  
After fix: `I have an idea for one more agent`

Original: `gonna send this later probs`  
After rewrite: `I will send this later, probably`

### Shell Agent

Intelligent shell history curator that removes noise and duplicates while keeping everything important.

**Commands:**

```bash
# Preview what would be removed (safe, no changes)
agb shell purge

# Actually purge history
agb shell purge --no-preview

# Restore from latest backup
agb shell restore

# List available backups
agb shell backups

# Use custom history file
agb shell purge --history-file ~/.bash_history
```

**What gets removed:**
- Exact duplicates (keeps first occurrence)
- Simple noise commands: `ls`, `cd`, `pwd`, `clear`, `exit`
- Commands older than 7 days that match removal rules

**What always stays:**
- Recent commands (last 7 days are untouched)
- Complex commands (pipes, redirects, command chains)
- Unique commands (first occurrence)
- Commands with multiple flags
- Long commands (>50 characters)

**Safety features:**
- Automatic timestamped backup before every purge
- Preview mode by default (use `--no-preview` to actually modify)
- Atomic writes (all-or-nothing)
- Easy restore from backup
- Purge log tracks what was removed and why

**Example workflow:**

```bash
# 1. Preview what would be removed
$ agb shell purge
🔍 Preview mode - no changes will be made

      Purge Preview       
┌────────────────┬───────┐
│ Metric         │ Count │
├────────────────┼───────┤
│ Total commands │ 10000 │
│ Will keep      │ 2500  │
│ Will remove    │ 7500  │
│ % removed      │ 75.0% │
└────────────────┴───────┘

# 2. Looks good? Actually purge
$ agb shell purge --no-preview
✅ Purge complete!
   Kept: 2,500 commands
   Removed: 7,500 commands
   Backup: ~/.zsh_history.backup.2026-02-09_14-23-45

# 3. If needed, restore from backup
$ agb shell restore
✅ Restored from: ~/.zsh_history.backup.2026-02-09_14-23-45
```

### Gmail Agent (Coming Soon)

Automatically classify and tag spam/promotional emails.

```bash
agb gmail clean --dry-run
agb gmail clean --from-date 2026-02-01
```

## Configuration

### Environment Variables

Create a `.env` file in your project root:

```bash
# Copy example file
cp .env.example .env

# Edit as needed
AB_OLLAMA_MODEL=llama3.2:3b
AB_OLLAMA_URL=http://localhost:11434
AB_TEXT_SHOW_PREVIEW=true
```

### Available Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `AB_OLLAMA_MODEL` | `llama3.2:3b` | Ollama model to use |
| `AB_OLLAMA_URL` | `http://localhost:11434` | Ollama server URL |
| `AB_TEXT_SHOW_PREVIEW` | `true` | Show before/after preview |
| `AB_LOG_LEVEL` | `INFO` | Logging level |

## Project Structure

```
agb/
├── src/
│   └── ab/
│       ├── __init__.py
│       ├── __main__.py         # CLI entry point
│       ├── core/               # Shared infrastructure
│       │   ├── ollama_client.py
│       │   ├── config.py
│       │   └── logging.py
│       └── agents/
│           └── text/           # Text agent
│               ├── checker.py
│               ├── clipboard.py
│               └── commands.py
├── data/                       # Runtime data (gitignored)
├── pyproject.toml
└── README.md
```

## Development

### Adding a New Agent

1. **Create agent directory**:
   ```
   src/ab/agents/myagent/
   ├── __init__.py
   ├── agent.py
   └── commands.py
   ```

2. **Implement commands** (`commands.py`):
   ```python
   import click
   from ab.core import OllamaClient, get_settings
   
   @click.group(name="myagent")
   def myagent_group():
       """My agent description."""
       pass
   
   @myagent_group.command(name="action")
   @click.option("--option", help="Some option")
   def action(option):
       """Do something."""
       settings = get_settings()
       ollama = OllamaClient(settings.ollama_model, settings.ollama_url)
       # Your agent logic here
   ```

3. **Register in main CLI** (`__main__.py`):
   ```python
   from ab.agents.myagent.commands import myagent_group
   main.add_command(myagent_group)
   ```

4. **Use it**:
   ```bash
   agb myagent action --option value
   ```

### Running Tests

```bash
# Install dev dependencies
pipx install -e ".[dev]"

# Run tests
pytest

# With coverage
pytest --cov=ab
```

### Code Quality

```bash
# Format code
black src/

# Lint
ruff check src/
```

## Troubleshooting

### "Cannot connect to Ollama"

Make sure Ollama is running:
```bash
ollama serve
```

### "Model not found"

Pull the model:
```bash
ollama pull llama3.2:3b
```

### "Clipboard is empty"

Make sure you've copied text (Cmd+C) before running text commands.

### Permissions Error (macOS)

Grant Terminal access to clipboard in System Settings > Privacy & Security > Automation.

## CLI Help

```bash
$ agb --help
Usage: agb [OPTIONS] COMMAND [ARGS]...

  AB - Personal AI agents for productivity.
  
  Fast, local AI agents powered by Ollama.

Options:
  --version          Show version
  -v, --verbose      Verbose logging
  --help             Show this message

Commands:
  findtab  Find That Tab - Semantic browser history search
  shell    Shell history management commands
  text     Text grammar and typo checker

$ agb shell --help
Usage: agb shell [OPTIONS] COMMAND [ARGS]...

  Shell history management commands.

Commands:
  backups  List available backups
  purge    Purge noise and duplicates from shell history
  restore  Restore history from backup

$ agb shell purge --help
Usage: agb shell purge [OPTIONS]

  Purge noise and duplicates from shell history.

  By default, shows a preview without making changes.
  Use --no-preview to actually modify history.

Options:
  --preview / --no-preview  Preview changes without modifying history
                            (default: preview)
  --history-file PATH       Path to zsh history file
                            (default: ~/.zsh_history)
  --help                    Show this message
```

## Performance

- **Speed**: 1-2 seconds per request (with llama3.2:3b)
- **Privacy**: 100% local processing
- **Offline**: Works without internet (after model download)
- **Cost**: Free (uses local Ollama)

## Roadmap

- [x] Text agent (grammar/typo checker)
- [x] Shell agent (history curator)
- [x] FindTab agent (semantic browser history search)
- [ ] Gmail agent (spam classifier)
- [ ] Calendar agent (meeting summarizer)
- [ ] File organizer agent
- [ ] Code review agent
- [ ] Notes search agent

## License

MIT

## Contributing

1. Add your agent to `src/ab/agents/`
2. Register it in `__main__.py`
3. Add tests
4. Update documentation
5. Submit PR

## Why "agb"?

Short for **Agent Box** - quick to type, easy to remember. Three letters like other CLI tools (`git`, `npm`, `aws`, etc.).
