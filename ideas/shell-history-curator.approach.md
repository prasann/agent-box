# Shell History Curator - Technical Approach

## Overview
Intelligent shell history organizer that cleans, classifies, and curates terminal history without breaking muscle memory or leaking secrets. Uses Ollama (local LLM) for intent-based classification and deduplication.

## Core Philosophy: Classification First, Safety Always

**Golden Rule**: Never mutate `~/.zsh_history` directly. Read from it, but write to separate outputs.

**Primary Goal**: Reduce noise, preserve intent, protect sensitive data, keep recall useful.

## User Flow

1. Run terminal command: `hc analyze` (history curator analyze)
2. Agent reads `~/.zsh_history`
3. Classifies commands into buckets
4. Generates curated outputs:
   - `~/.history_golden` - High-value reusable commands
   - `~/.history_patterns` - Command patterns by intent
   - `~/.history_report` - Insights and suggestions
5. Integration with shell search (Ctrl+R)

**Use Cases**:
- Find that complex command you typed 3 months ago
- Learn your own command patterns
- Build a "greatest hits" command library
- Clean up clutter without losing important commands
- Ensure secrets never show up in curated lists

**Frequency**: Weekly or on-demand

## Architecture

```
┌──────────────────────┐
│  ~/.zsh_history      │
│  (read-only input)   │
└──────────┬───────────┘
           │
           ▼
    ┌──────────────┐
    │  Python CLI  │
    │  (hc)        │
    └──────┬───────┘
           │
           ├─────────────────┐
           │                 │
           ▼                 ▼
      ┌──────────┐     ┌─────────────┐
      │  Ollama  │     │ Classifier  │
      │  Local   │     │ Rules       │
      └──────────┘     └─────────────┘
           │                 │
           └────────┬────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │  Output Generation  │
         ├─────────────────────┤
         │ • Golden commands   │
         │ • Patterns          │
         │ • Insights          │
         │ • Search index      │
         └─────────────────────┘
```

## Command Classification Strategy

### 1. Define Buckets (Not Deletions)

```python
class CommandBucket(str, Enum):
    REPETITIVE_NOISE = "noise"          # ls, cd, pwd, clear
    PARAMETERIZED_REPEAT = "repeat"     # kubectl get pod X/Y/Z
    ONE_OFF_EXPLORATION = "exploration" # Long pipes, experiments
    HIGH_VALUE = "golden"               # Setup, debugging, migrations
    SENSITIVE = "sensitive"             # Tokens, passwords, ssh
```

### 2. Classification Rules (Layered Approach)

**Layer 1: Pattern-based (Fast, No LLM)**

```python
# Noise patterns
NOISE_COMMANDS = {'ls', 'cd', 'pwd', 'clear', 'exit', 'history'}

# Sensitive patterns (regex)
SENSITIVE_PATTERNS = [
    r'(password|token|secret|key|auth)=',
    r'export \w*(PASSWORD|TOKEN|SECRET|KEY)',
    r'--password',
    r'(ssh|scp).+@.+',
    r'(curl|wget).+-H.*Authorization',
    r'echo.*\$.*KEY',
]

# High-value indicators
HIGH_VALUE_INDICATORS = [
    'docker-compose', 'kubectl apply', 'terraform',
    'git clone', 'brew install', 'pipx install',
    'systemctl', 'nginx', 'postgres',
]
```

**Layer 2: LLM-based (Intent Understanding)**

```python
def classify_with_llm(command: str) -> ClassificationResult:
    """Use Ollama to understand command intent."""
    prompt = f"""Classify this shell command into ONE category:

Categories:
- noise: Simple, repetitive commands (ls, cd, pwd)
- repeat: Same command with different parameters
- exploration: One-off experiment or complex pipe
- golden: Valuable, reusable command worth saving
- sensitive: Contains passwords, tokens, keys, or secrets

Command: {command}

Respond with ONLY the category name and a brief reason.
Format: category: reason"""
    
    response = ollama.generate(prompt, temperature=0.1)
    return parse_classification(response)
```

**Layer 3: Deduplication by Intent**

Instead of removing exact duplicates:

```python
# Before (naive)
commands = [
    "kubectl get pod foo",
    "kubectl get pod bar",
    "kubectl get pod baz",
]
# Result: Keep only one? Lose the others?

# After (intent-based)
pattern = "kubectl get pod <name>"
examples = ["foo", "bar", "baz"]
golden_entry = {
    "pattern": pattern,
    "description": "Get pod status by name",
    "examples": examples[:3],  # Keep a few examples
    "frequency": 45,
}
```

## Sensitive Data Handling ☢️

**Zero-tolerance policy**: Never summarize, paraphrase, or store commands with secrets.

### Detection Strategy

```python
def is_sensitive(command: str) -> tuple[bool, str]:
    """Check if command contains sensitive data."""
    
    # 1. Pattern matching
    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, command):
            return True, f"Matches pattern: {pattern}"
    
    # 2. Environment variables
    if re.search(r'\$\w*(PASSWORD|TOKEN|SECRET|KEY|AUTH)', command):
        return True, "Contains sensitive env var"
    
    # 3. Known secret locations
    secret_paths = ['/secrets/', '.env', 'credentials', '.pem', '.key']
    if any(path in command for path in secret_paths):
        return True, "References secret file"
    
    # 4. LLM double-check (for edge cases)
    llm_check = check_sensitivity_with_llm(command)
    
    return llm_check.is_sensitive, llm_check.reason
```

### Handling Options

```python
class SensitiveCommandHandler:
    def handle(self, command: str, reason: str) -> HandledCommand:
        """Safely handle sensitive command."""
        
        options = {
            "exclude": None,  # Don't include anywhere
            "placeholder": "command_with_sensitive_args",
            "redacted": redact_sensitive_parts(command),
        }
        
        # Default: Exclude entirely
        return options["exclude"]
```

## Output Formats

### 1. Golden Commands (`~/.history_golden`)

```bash
# Shell History Curator - Golden Commands
# Generated: 2026-02-06
# Total valuable commands: 127

# === Development Setup ===

# Start local development environment
docker-compose up -d postgres redis

# Reset database and run migrations
psql -U postgres -c "DROP DATABASE app_db; CREATE DATABASE app_db;" && alembic upgrade head

# === Kubernetes ===

# Get pod logs with follow
kubectl logs -f deployment/<name> -n <namespace>

# Port forward to service
kubectl port-forward service/<name> <local-port>:<remote-port> -n <namespace>

# === Git ===

# Interactive rebase last N commits
git rebase -i HEAD~<N>

# Sync fork with upstream
git fetch upstream && git rebase upstream/main && git push origin main --force-with-lease
```

### 2. Command Patterns (`~/.history_patterns.json`)

```json
{
  "patterns": [
    {
      "id": "kubectl-get-pod",
      "pattern": "kubectl get pod <name> -n <namespace>",
      "description": "Get pod status in namespace",
      "category": "kubernetes",
      "frequency": 45,
      "examples": ["prod", "staging", "dev"],
      "last_used": "2026-02-05"
    },
    {
      "id": "docker-exec",
      "pattern": "docker exec -it <container> /bin/bash",
      "description": "Interactive shell in container",
      "category": "docker",
      "frequency": 23,
      "examples": ["postgres", "redis", "app"],
      "last_used": "2026-02-06"
    }
  ]
}
```

### 3. Insights Report (`~/.history_report.md`)

```markdown
# Shell History Analysis Report
Generated: 2026-02-06

## Summary
- Total commands analyzed: 12,456
- Unique commands: 3,421
- Golden commands: 127
- Patterns identified: 34
- Sensitive commands detected: 18 (excluded)

## Top Command Categories
1. Kubernetes (23%)
2. Git operations (18%)
3. Docker (12%)
4. File operations (11%)
5. Text processing (8%)

## High-Value Commands (Recently Used)
- `kubectl port-forward service/api 8080:80` (3 times this week)
- `docker-compose logs -f --tail=100 api` (5 times this week)
- `git log --oneline --graph --all` (2 times this week)

## Patterns You Should Save
1. **Database migrations**: Used 15 times with variations
   - Suggested alias: `alias migrate-reset="./scripts/reset-db.sh"`

2. **Log tailing**: Used 23 times with variations
   - Suggested function: `klogs() { kubectl logs -f deployment/$1 }`

## Noise Reduction
- Removed 8,234 repetitive commands (ls, cd, pwd)
- Deduplicated 1,567 parameterized commands
- Excluded 18 sensitive commands

## Recommendations
- Consider creating aliases for top 10 frequently used commands
- Package "port-forward" pattern into a shell function
- Your kubectl commands follow consistent patterns - great for automation!
```

### 4. Searchable Index (for integration)

```json
{
  "index": {
    "version": "1.0",
    "generated": "2026-02-06T10:30:00Z",
    "entries": [
      {
        "id": "cmd_001",
        "command": "kubectl get pods -n production",
        "timestamp": "2026-02-05T14:22:00Z",
        "category": "kubernetes",
        "tags": ["k8s", "pods", "production"],
        "description": "List pods in production namespace",
        "is_sensitive": false
      }
    ]
  }
}
```

## Implementation: Python CLI Tool

### File Structure
```
shell-history-curator/
├── pyproject.toml
├── README.md
├── .gitignore
├── src/
│   └── history_curator/
│       ├── __init__.py
│       ├── __main__.py          # Entry point (hc command)
│       ├── parser.py            # Parse zsh_history
│       ├── classifier.py        # Command classification
│       ├── sensitive_detector.py # Sensitive data detection
│       ├── deduplicator.py      # Intent-based dedup
│       ├── generator.py         # Output generation
│       ├── ollama_client.py     # Shared with other agents
│       ├── models.py            # Pydantic models
│       ├── config.py            # Settings
│       └── patterns/
│           ├── noise.py         # Noise patterns
│           ├── sensitive.py     # Sensitive patterns
│           └── high_value.py    # High-value indicators
└── tests/
    ├── test_classifier.py
    ├── test_sensitive_detector.py
    └── test_parser.py
```

### Dependencies (pyproject.toml)

```toml
[project]
name = "shell-history-curator"
version = "0.1.0"
description = "Intelligent shell history organizer"
dependencies = [
    "requests",
    "pydantic>=2.0",
    "pydantic-settings",
    "python-dotenv",
    "rich",           # Terminal output
    "click",          # CLI framework
    "dateutil",       # Date parsing
]

[project.scripts]
hc = "history_curator.__main__:cli"

[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-cov",
    "black",
    "ruff",
]
```

### Core Code: `parser.py`

```python
"""Parse zsh history file."""
import re
from datetime import datetime
from pathlib import Path
from typing import Iterator
from .models import HistoryEntry

class ZshHistoryParser:
    """Parser for zsh extended history format."""
    
    # Format: : <timestamp>:<elapsed>;<command>
    EXTENDED_PATTERN = re.compile(r'^: (\d+):(\d+);(.*)$')
    
    def __init__(self, history_file: Path = None):
        self.history_file = history_file or Path.home() / '.zsh_history'
    
    def parse(self) -> Iterator[HistoryEntry]:
        """Parse history file and yield entries."""
        if not self.history_file.exists():
            raise FileNotFoundError(f"History file not found: {self.history_file}")
        
        with open(self.history_file, 'r', errors='replace') as f:
            for line in f:
                line = line.rstrip('\n')
                
                # Try extended format first
                match = self.EXTENDED_PATTERN.match(line)
                if match:
                    timestamp = int(match.group(1))
                    elapsed = int(match.group(2))
                    command = match.group(3)
                    
                    yield HistoryEntry(
                        command=command,
                        timestamp=datetime.fromtimestamp(timestamp),
                        elapsed_seconds=elapsed,
                    )
                else:
                    # Simple format (no timestamp)
                    yield HistoryEntry(
                        command=line,
                        timestamp=None,
                        elapsed_seconds=None,
                    )
```

### Core Code: `classifier.py`

```python
"""Command classification engine."""
from typing import List
from .models import HistoryEntry, CommandBucket, ClassificationResult
from .ollama_client import OllamaClient
from .patterns import NOISE_COMMANDS, SENSITIVE_PATTERNS, HIGH_VALUE_INDICATORS

class CommandClassifier:
    def __init__(self, ollama_client: OllamaClient):
        self.ollama = ollama_client
    
    def classify(self, entry: HistoryEntry) -> ClassificationResult:
        """Classify a command using layered approach."""
        
        # Layer 1: Fast pattern matching
        if self._is_noise(entry.command):
            return ClassificationResult(
                entry=entry,
                bucket=CommandBucket.REPETITIVE_NOISE,
                reason="Simple repetitive command",
                confidence=1.0,
            )
        
        if self._is_sensitive(entry.command):
            return ClassificationResult(
                entry=entry,
                bucket=CommandBucket.SENSITIVE,
                reason="Contains sensitive data",
                confidence=1.0,
            )
        
        if self._is_high_value(entry.command):
            # High confidence, but still check with LLM
            pass
        
        # Layer 2: LLM classification
        return self._classify_with_llm(entry)
    
    def _is_noise(self, command: str) -> bool:
        """Check if command is noise."""
        base_cmd = command.split()[0] if command.split() else ""
        return base_cmd in NOISE_COMMANDS
    
    def _is_sensitive(self, command: str) -> bool:
        """Check if command contains sensitive data."""
        import re
        for pattern in SENSITIVE_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return True
        return False
    
    def _is_high_value(self, command: str) -> bool:
        """Check if command has high-value indicators."""
        return any(indicator in command for indicator in HIGH_VALUE_INDICATORS)
    
    def _classify_with_llm(self, entry: HistoryEntry) -> ClassificationResult:
        """Use LLM for nuanced classification."""
        prompt = f"""Classify this shell command:

Command: {entry.command}

Categories:
- noise: Simple, repetitive (ls, cd, pwd)
- repeat: Same command, different params
- exploration: One-off experiment
- golden: Valuable, reusable command
- sensitive: Contains secrets

Respond: category: reason"""
        
        response = self.ollama.generate(
            prompt=prompt,
            temperature=0.1,  # Low temp for consistency
        )
        
        # Parse response
        bucket, reason = self._parse_llm_response(response)
        
        return ClassificationResult(
            entry=entry,
            bucket=bucket,
            reason=reason,
            confidence=0.85,  # LLM confidence
        )
    
    def _parse_llm_response(self, response: str) -> tuple[CommandBucket, str]:
        """Parse LLM classification response."""
        # Simple parsing: "category: reason"
        parts = response.strip().split(':', 1)
        if len(parts) == 2:
            category = parts[0].strip().lower()
            reason = parts[1].strip()
            
            bucket_map = {
                'noise': CommandBucket.REPETITIVE_NOISE,
                'repeat': CommandBucket.PARAMETERIZED_REPEAT,
                'exploration': CommandBucket.ONE_OFF_EXPLORATION,
                'golden': CommandBucket.HIGH_VALUE,
                'sensitive': CommandBucket.SENSITIVE,
            }
            
            return bucket_map.get(category, CommandBucket.ONE_OFF_EXPLORATION), reason
        
        return CommandBucket.ONE_OFF_EXPLORATION, "Unable to classify"
```

### Core Code: `deduplicator.py`

```python
"""Intent-based deduplication."""
from collections import defaultdict
from typing import List
from .models import HistoryEntry, CommandPattern
from .ollama_client import OllamaClient

class IntentDeduplicator:
    """Deduplicate commands by intent, not exact match."""
    
    def __init__(self, ollama_client: OllamaClient):
        self.ollama = ollama_client
    
    def deduplicate(self, entries: List[HistoryEntry]) -> List[CommandPattern]:
        """Group similar commands into patterns."""
        
        # Group by base command first
        groups = defaultdict(list)
        for entry in entries:
            base_cmd = self._get_base_command(entry.command)
            groups[base_cmd].append(entry)
        
        patterns = []
        for base_cmd, group_entries in groups.items():
            if len(group_entries) <= 3:
                # Few commands, keep as-is
                for entry in group_entries:
                    patterns.append(CommandPattern.from_single_entry(entry))
            else:
                # Many commands, extract pattern
                pattern = self._extract_pattern(group_entries)
                patterns.append(pattern)
        
        return patterns
    
    def _get_base_command(self, command: str) -> str:
        """Extract base command (first 2-3 tokens)."""
        parts = command.split()
        if len(parts) <= 2:
            return ' '.join(parts)
        return ' '.join(parts[:3])
    
    def _extract_pattern(self, entries: List[HistoryEntry]) -> CommandPattern:
        """Use LLM to extract command pattern."""
        
        # Sample up to 10 commands
        samples = [e.command for e in entries[:10]]
        
        prompt = f"""Extract a command pattern from these similar commands:

{chr(10).join(f"- {cmd}" for cmd in samples)}

Create a pattern with placeholders like <name>, <path>, <port>, etc.

Respond with:
Pattern: <pattern>
Description: <one-line description>"""
        
        response = self.ollama.generate(
            prompt=prompt,
            temperature=0.2,
        )
        
        # Parse response
        pattern, description = self._parse_pattern_response(response)
        
        return CommandPattern(
            pattern=pattern,
            description=description,
            examples=[e.command for e in entries[:5]],
            frequency=len(entries),
            category=self._infer_category(pattern),
        )
    
    def _parse_pattern_response(self, response: str) -> tuple[str, str]:
        """Parse LLM pattern extraction response."""
        lines = response.strip().split('\n')
        pattern = ""
        description = ""
        
        for line in lines:
            if line.startswith('Pattern:'):
                pattern = line.split(':', 1)[1].strip()
            elif line.startswith('Description:'):
                description = line.split(':', 1)[1].strip()
        
        return pattern, description
    
    def _infer_category(self, pattern: str) -> str:
        """Infer command category from pattern."""
        categories = {
            'kubernetes': ['kubectl', 'k8s'],
            'docker': ['docker', 'docker-compose'],
            'git': ['git'],
            'database': ['psql', 'mysql', 'mongo'],
            'network': ['curl', 'wget', 'netstat', 'ping'],
        }
        
        pattern_lower = pattern.lower()
        for category, keywords in categories.items():
            if any(kw in pattern_lower for kw in keywords):
                return category
        
        return 'general'
```

### Core Code: `generator.py`

```python
"""Generate output files from classified commands."""
from pathlib import Path
from datetime import datetime
from typing import List
from .models import ClassificationResult, CommandPattern, CommandBucket

class OutputGenerator:
    """Generate various output formats."""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path.home()
    
    def generate_golden_commands(self, results: List[ClassificationResult]) -> Path:
        """Generate golden commands file."""
        output_file = self.output_dir / '.history_golden'
        
        # Filter golden commands
        golden = [r for r in results if r.bucket == CommandBucket.HIGH_VALUE]
        
        # Sort by category and frequency
        golden.sort(key=lambda r: (r.entry.category or 'other', -r.entry.frequency))
        
        with open(output_file, 'w') as f:
            f.write(f"# Shell History Curator - Golden Commands\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write(f"# Total valuable commands: {len(golden)}\n\n")
            
            current_category = None
            for result in golden:
                category = result.entry.category or 'Other'
                if category != current_category:
                    f.write(f"\n# === {category.title()} ===\n\n")
                    current_category = category
                
                # Write command with description
                if result.reason:
                    f.write(f"# {result.reason}\n")
                f.write(f"{result.entry.command}\n\n")
        
        return output_file
    
    def generate_patterns(self, patterns: List[CommandPattern]) -> Path:
        """Generate patterns JSON file."""
        import json
        
        output_file = self.output_dir / '.history_patterns.json'
        
        data = {
            "patterns": [p.dict() for p in patterns],
            "generated": datetime.now().isoformat(),
            "total": len(patterns),
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return output_file
    
    def generate_report(self, results: List[ClassificationResult], 
                       patterns: List[CommandPattern]) -> Path:
        """Generate insights report."""
        output_file = self.output_dir / '.history_report.md'
        
        # Calculate statistics
        total = len(results)
        by_bucket = {}
        for bucket in CommandBucket:
            by_bucket[bucket] = len([r for r in results if r.bucket == bucket])
        
        with open(output_file, 'w') as f:
            f.write(f"# Shell History Analysis Report\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d')}\n\n")
            
            f.write(f"## Summary\n")
            f.write(f"- Total commands analyzed: {total:,}\n")
            f.write(f"- Golden commands: {by_bucket[CommandBucket.HIGH_VALUE]}\n")
            f.write(f"- Patterns identified: {len(patterns)}\n")
            f.write(f"- Sensitive commands detected: {by_bucket[CommandBucket.SENSITIVE]} (excluded)\n")
            f.write(f"- Noise filtered: {by_bucket[CommandBucket.REPETITIVE_NOISE]}\n\n")
            
            # More sections...
            # (Top categories, recommendations, etc.)
        
        return output_file
```

### Entry Point: `__main__.py`

```python
"""CLI entry point for history curator."""
import click
from rich.console import Console
from pathlib import Path
from .parser import ZshHistoryParser
from .classifier import CommandClassifier
from .deduplicator import IntentDeduplicator
from .generator import OutputGenerator
from .ollama_client import OllamaClient
from .config import Settings

console = Console()

@click.group()
def cli():
    """Shell History Curator - Intelligent history organizer"""
    pass

@cli.command()
@click.option('--history-file', type=Path, help='Path to zsh history file')
@click.option('--output-dir', type=Path, help='Output directory')
def analyze(history_file, output_dir):
    """Analyze shell history and generate curated outputs."""
    
    console.print("🔍 Analyzing shell history...", style="bold blue")
    
    # Initialize
    settings = Settings()
    ollama = OllamaClient(
        model=settings.ollama_model,
        base_url=settings.ollama_url,
    )
    
    # Check Ollama availability
    if not ollama.is_available():
        console.print("❌ Ollama is not running", style="bold red")
        console.print("Start it with: ollama serve", style="yellow")
        return
    
    # Parse history
    parser = ZshHistoryParser(history_file)
    entries = list(parser.parse())
    console.print(f"📊 Found {len(entries):,} commands", style="green")
    
    # Classify
    classifier = CommandClassifier(ollama)
    console.print("🏷️  Classifying commands...", style="bold blue")
    
    results = []
    with console.status("[bold blue]Processing...") as status:
        for i, entry in enumerate(entries):
            result = classifier.classify(entry)
            results.append(result)
            
            if i % 100 == 0:
                status.update(f"[bold blue]Processed {i}/{len(entries)}")
    
    # Deduplicate
    console.print("🔄 Deduplicating by intent...", style="bold blue")
    deduplicator = IntentDeduplicator(ollama)
    golden_entries = [r.entry for r in results if r.bucket.value == 'golden']
    patterns = deduplicator.deduplicate(golden_entries)
    
    # Generate outputs
    console.print("📝 Generating outputs...", style="bold blue")
    generator = OutputGenerator(output_dir)
    
    golden_file = generator.generate_golden_commands(results)
    patterns_file = generator.generate_patterns(patterns)
    report_file = generator.generate_report(results, patterns)
    
    # Summary
    console.print("\n✅ Analysis complete!", style="bold green")
    console.print(f"\nGenerated files:")
    console.print(f"  • Golden commands: {golden_file}")
    console.print(f"  • Patterns: {patterns_file}")
    console.print(f"  • Report: {report_file}")

@cli.command()
def search():
    """Interactive search of curated history."""
    # TODO: Implement fuzzy search using fzf or similar
    console.print("🔍 Interactive search (coming soon)", style="yellow")

@cli.command()
@click.argument('pattern')
def find(pattern):
    """Find commands matching a pattern."""
    # TODO: Search through golden commands and patterns
    console.print(f"Searching for: {pattern}", style="blue")

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
   cd shell-history-curator
   pipx install .
   ```

3. **Run analysis**:
   ```bash
   # First time (will take a while)
   hc analyze
   
   # Check the report
   cat ~/.history_report.md
   
   # View golden commands
   less ~/.history_golden
   ```

4. **Optional: Schedule weekly analysis**:
   ```bash
   # Add to crontab
   crontab -e
   
   # Run every Sunday at 10 AM
   0 10 * * 0 /Users/<your-username>/.local/bin/hc analyze
   ```

## Usage Examples

```bash
# Basic analysis
hc analyze

# Custom history file
hc analyze --history-file ~/.zsh_history.bak

# Custom output directory
hc analyze --output-dir ~/history-analysis

# Future: Interactive search
hc search
# > Shows fzf interface with golden commands and patterns

# Future: Find specific pattern
hc find "kubectl"
# Shows all kubectl-related patterns and commands
```

## Integration Ideas

### 1. Shell Search (Ctrl+R) Integration

```bash
# Add to ~/.zshrc
# Use golden commands for Ctrl+R
export HISTORY_IGNORE_SPACE=1

# Custom search function
function hcs() {
  # Search golden commands
  cat ~/.history_golden | grep -v '^#' | fzf --preview 'echo {}' | pbcopy
}
```

### 2. Auto-alias Generation

```bash
# Add to ~/.zshrc
# Source auto-generated aliases
[[ -f ~/.history_aliases ]] && source ~/.history_aliases
```

Agent generates `~/.history_aliases`:
```bash
# Auto-generated aliases from history analysis
# Generated: 2026-02-06

alias k='kubectl'
alias kg='kubectl get'
alias kgp='kubectl get pods'
alias klogs='kubectl logs -f'
alias dc='docker-compose'
alias dcu='docker-compose up -d'
alias dcd='docker-compose down'
```

### 3. Command Recommendation Engine

Future enhancement: As you type, suggest from your golden commands.

```bash
# Add to ~/.zshrc with zsh-autosuggestions
ZSH_AUTOSUGGEST_STRATEGY=(history golden)

# Custom strategy that reads from ~/.history_golden
```

## Performance Considerations

- **Initial analysis**: 
  - 10,000 commands: ~5-10 minutes (with LLM)
  - 50,000 commands: ~30-40 minutes
  
- **Optimization strategies**:
  - Batch LLM calls (10 commands at once)
  - Cache classification results
  - Skip noise commands entirely
  - Only LLM-classify ambiguous commands

- **Incremental updates**:
  - Store last processed timestamp
  - Only analyze new commands
  - Update patterns incrementally

## Safety Features

### 1. Read-Only History File

```python
# NEVER EVER do this
with open('~/.zsh_history', 'w') as f:  # ❌ FORBIDDEN
    f.write(...)

# Always do this
with open('~/.zsh_history', 'r') as f:  # ✅ Safe
    data = f.read()
```

### 2. Sensitive Command Isolation

```python
# Sensitive commands go to separate, encrypted file (optional)
sensitive_log = Path.home() / '.history_sensitive.gpg'

# Or just exclude entirely (safer)
# Never write sensitive commands anywhere
```

### 3. Backup Before First Run

```bash
# Auto-backup in the tool
def backup_history():
    """Backup history file before first run."""
    history_file = Path.home() / '.zsh_history'
    backup_file = Path.home() / f'.zsh_history.backup.{timestamp}'
    shutil.copy(history_file, backup_file)
    console.print(f"✅ Backup created: {backup_file}")
```

## Privacy Features

- **100% Local**: All processing with Ollama
- **No Cloud**: Commands never leave your machine
- **No Logging**: Agent doesn't log your commands anywhere external
- **User Control**: All outputs are local files you control

## Comparison to Existing Tools

| Feature | This Solution | `history | grep` | McFly | Atuin |
|---------|---------------|-------------------|-------|-------|
| Intent-based | Yes | No | No | No |
| Pattern extraction | Yes | No | No | No |
| Sensitive detection | Yes | No | No | No |
| LLM-powered | Yes | No | No | No |
| Cloud sync | No | No | No | Optional |
| Local-only | Yes | Yes | Yes | Optional |
| Curated output | Yes | No | Partial | No |
| Learning/insights | Yes | No | Limited | Limited |

**Best for**: Users who want intelligent organization and insights from their history, with strong privacy guarantees.

## Estimated Development Time

- Project setup (same structure): 30 minutes
- History parser: 1 hour
- Classification engine: 2 hours
- Sensitive detector: 1.5 hours
- Deduplicator (intent-based): 2 hours
- Output generators: 2 hours
- CLI interface: 1 hour
- Testing: 2 hours
- **Total**: ~12 hours (includes proper structure)

## Future Enhancements

1. **Command Recommendation**: As-you-type suggestions from golden commands
2. **Auto-alias Generation**: Automatically create aliases for frequent patterns
3. **Team Sharing**: Export golden commands to share with team (with privacy controls)
4. **Shell Integration**: Deep integration with zsh/fzf for better search
5. **Analytics Dashboard**: Web UI showing history trends and patterns
6. **Command Templates**: Generate reusable command templates from patterns
7. **Encrypted Storage**: Option to encrypt sensitive command log

## Why This Approach Works

✅ **Safe**: Never mutates original history  
✅ **Smart**: Intent-based, not just text matching  
✅ **Private**: 100% local with Ollama  
✅ **Useful**: Produces actionable outputs  
✅ **Reversible**: All operations are read-only  
✅ **Secure**: Sensitive command detection and isolation  
✅ **Learning**: Helps you understand your own patterns

## Limitations

- Initial analysis is slow (LLM classification takes time)
- Requires Ollama running locally
- Quality depends on LLM's understanding of shell commands
- Pattern extraction may need refinement based on your workflow
- Only works with zsh history format (could extend to bash)
