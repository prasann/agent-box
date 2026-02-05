# AB - Personal AI Agents

Single command-line tool (`agb`) that provides multiple AI agents as subcommands. Install once, get all your productivity agents.

## Features

- 🧠 **Local AI**: All processing via Ollama (private, fast, free)
- 🎯 **Simple CLI**: `agb <agent> <action>` - intuitive command structure
- 📦 **Unified Package**: Install once, get all agents
- 🔧 **Easy to Extend**: Add new agents in minutes
- 🎨 **Beautiful Output**: Rich terminal interface with colors and panels

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

# Get help
agb --help
agb text --help
```

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
  text  Text grammar and typo checker

$ agb text --help
Usage: agb text [OPTIONS] COMMAND [ARGS]...

  Text grammar and typo checker.

Commands:
  fix      Fix typos and grammar in clipboard text
  rewrite  Rewrite text in clipboard for clarity and professionalism

$ agb text fix --help
Usage: agb text fix [OPTIONS]

  Fix typos and grammar in clipboard text.

Options:
  --no-preview  Don't show before/after preview
  --help        Show this message
```

## Performance

- **Speed**: 1-2 seconds per request (with llama3.2:3b)
- **Privacy**: 100% local processing
- **Offline**: Works without internet (after model download)
- **Cost**: Free (uses local Ollama)

## Roadmap

- [x] Text agent (grammar/typo checker)
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
