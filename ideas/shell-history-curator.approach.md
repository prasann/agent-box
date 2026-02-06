# Shell History Curator - Technical Approach

## Overview
Intelligent shell history purger that removes noise and duplicates from terminal history while keeping everything important. Uses Ollama (local LLM) only for edge cases - most purging is rule-based and safe.

## Core Philosophy: Safety First, Simple Always

**Golden Rule**: Multiple backups before any modification. Conservative by default.

**Primary Goal**: Remove obvious clutter, keep everything else. Make Ctrl+R useful again.

## User Flow

1. Run terminal command: `hc purge --preview` (see what would be removed)
2. Review the preview, looks good
3. Run: `hc purge` (actually removes noise)
4. History file is now cleaner, Ctrl+R is more useful

**What gets removed (Low Risk Only)**:
- Exact duplicates (even complex commands)
- Simple noise commands: `ls`, `cd`, `pwd`, `clear`, `exit`
- Commands that failed (exit code != 0, if detectable)
- Obvious typos followed by corrections

**What always stays**:
- Unique commands (show up only once)
- Complex commands (pipes, multiple commands, flags)
- Recent commands (last 7 days are untouched)
- Anything remotely unusual or interesting

**Safety mechanisms**:
- Automatic timestamped backup before every purge
- `--preview` mode (default: shows what will happen)
- Purge log (what was removed and why)
- Easy restore: `hc restore`

**Frequency**: Monthly or when history feels cluttered

## Architecture

```
┌──────────────────────┐
│  ~/.zsh_history      │
│  (10,000 commands)   │
└──────────┬───────────┘
           │
           ▼
    ┌──────────────┐
    │  Python CLI  │
    │  (hc purge)  │
    └──────┬───────┘
           │
           ├─ Create backup: ~/.zsh_history.backup.2026-02-06
           │
           ▼
      ┌──────────────────┐
      │  Rule-based      │
      │  Classifier      │
      │  (fast, safe)    │
      └──────┬───────────┘
             │
             ├─ Exact duplicates → Remove
             ├─ Simple commands  → Remove
             ├─ Recent commands  → Keep
             └─ Everything else  → Keep
             │
             ▼
         ┌───────────────────┐
         │  Write new file   │
         │  (atomic write)   │
         └───────────────────┘
              │
              ├─ ~/.zsh_history (cleaned)
              └─ ~/.zsh_history_purged.log (what was removed)
```

## Purge Strategy (Simple & Safe)

### What Gets Removed

**1. Exact Duplicates**
```python
# Keep first occurrence, remove subsequent identical commands
seen = set()
for entry in history:
    if entry.command in seen:
        remove(entry)  # Duplicate
    else:
        seen.add(entry.command)
        keep(entry)
```

**2. Simple Noise Commands**
```python
NOISE_COMMANDS = {
    'ls', 'ls -la', 'ls -l', 'll',
    'cd', 'cd ..', 'cd -',
    'pwd',
    'clear', 'cls',
    'exit', 'logout',
    'history',
}

if entry.command.strip() in NOISE_COMMANDS:
    remove(entry)
```

**3. Failed Commands (if detectable)**
```python
# Zsh extended history format includes exit codes
# Format: : timestamp:elapsed;command
if entry.exit_code != 0 and entry.command in seen_commands:
    remove(entry)  # Failed duplicate
```

**4. Obvious Typos Followed by Corrections**
```python
# If two consecutive commands are very similar (Levenshtein distance < 3)
# and the first failed, remove it
if is_similar(current, next) and current.exit_code != 0:
    remove(current)  # Likely typo
```

### What Always Stays

**1. Recent Commands (Last 7 Days)**
```python
cutoff = datetime.now() - timedelta(days=7)
if entry.timestamp > cutoff:
    keep(entry)  # Don't touch recent history
```

**2. Complex Commands**
```python
COMPLEXITY_INDICATORS = ['|', '&&', '||', ';', '$(', '`', '>', '>>', '<']

if any(indicator in entry.command for indicator in COMPLEXITY_INDICATORS):
    keep(entry)  # Complex command, probably important
```

**3. Commands with Multiple Flags**
```python
flag_count = entry.command.count(' -') + entry.command.count(' --')
if flag_count >= 2:
    keep(entry)  # Command with flags, probably intentional
```

**4. Long Commands**
```python
if len(entry.command) > 50:
    keep(entry)  # Long command, probably important
```

**5. Unique Commands (First Time Seen)**
```python
# Already handled in duplicate removal
# If it's the first occurrence, it stays
```

## Safety Mechanisms

### 1. Automatic Backups

```python
def create_backup(history_file: Path) -> Path:
    """Create timestamped backup before any modification."""
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    backup_file = history_file.parent / f'.zsh_history.backup.{timestamp}'
    shutil.copy2(history_file, backup_file)
    
    # Keep last 10 backups, remove older ones
    cleanup_old_backups(history_file.parent, keep=10)
    
    return backup_file
```

### 2. Atomic Writes

```python
def atomic_write_history(history_file: Path, entries: List[HistoryEntry]):
    """Write new history atomically (all-or-nothing)."""
    temp_file = history_file.parent / f'.zsh_history.tmp.{os.getpid()}'
    
    try:
        # Write to temp file first
        with open(temp_file, 'w') as f:
            for entry in entries:
                f.write(entry.to_zsh_format())
        
        # Verify temp file is valid
        verify_history_file(temp_file)
        
        # Atomic rename (replaces original)
        temp_file.rename(history_file)
    except Exception as e:
        temp_file.unlink(missing_ok=True)
        raise Exception(f"Failed to write history: {e}")
```

### 3. Purge Log

```python
def write_purge_log(removed_entries: List[HistoryEntry], reason_map: dict):
    """Log everything that was removed."""
    log_file = Path.home() / '.zsh_history_purged.log'
    
    with open(log_file, 'a') as f:
        f.write(f"\n# Purge: {datetime.now()}\n")
        f.write(f"# Removed: {len(removed_entries)} commands\n\n")
        
        for entry in removed_entries:
            reason = reason_map.get(entry.command, "unknown")
            f.write(f"# Reason: {reason}\n")
            f.write(f"{entry.command}\n")
```

### 4. Easy Restore

```python
def restore_backup(backup_file: Path = None):
    """Restore from backup."""
    if backup_file is None:
        # Find most recent backup
        backup_file = find_latest_backup()
    
    history_file = Path.home() / '.zsh_history'
    shutil.copy2(backup_file, history_file)
    
    console.print(f"✅ Restored from: {backup_file}")
```

## Output Files

### 1. Cleaned History (`~/.zsh_history`)

Your original history file, but with noise removed:

```bash
# Before purge: 10,000 commands
# After purge: 2,500 commands (75% noise removed)

# Commands are in zsh extended history format
: 1707217234:0;git status
: 1707217245:2;docker-compose up -d
: 1707217289:0;kubectl get pods -n production
...
```

### 2. Backup (`~/.zsh_history.backup.2026-02-06_14-23-45`)

Timestamped backup of original file before purge. Kept automatically.

### 3. Purge Log (`~/.zsh_history_purged.log`)

Record of what was removed and why:

```bash
# Purge: 2026-02-06 14:23:45
# Removed: 7,500 commands

# Reason: exact_duplicate (seen 45 times)
ls -la

# Reason: exact_duplicate (seen 23 times)
cd ..

# Reason: simple_noise
pwd

# Reason: exact_duplicate (seen 3 times)
kubectl get pods -n production

# Reason: failed_command (exit code: 127)
pythn script.py  # typo

...
```

## Implementation: Python CLI Tool

### File Structure
```
agb/
├── src/
│   └── ab/
│       ├── agents/
│       │   └── shell/
│       │       ├── __init__.py
│       │       ├── commands.py        # CLI commands (hc purge, hc restore)
│       │       ├── parser.py          # Parse zsh_history
│       │       ├── purger.py          # Purging logic
│       │       ├── rules.py           # Purge rules (what to remove)
│       │       └── models.py          # Pydantic models
│       │
│       └── core/
│           └── ollama_client.py       # Shared (not used for simple purging)
└── tests/
    ├── test_parser.py
    └── test_purger.py
```

### Dependencies (add to pyproject.toml)

```toml
# Already have most dependencies
# Just need click for CLI (may already have it)
dependencies = [
    "requests",
    "pydantic>=2.0",
    "pydantic-settings",
    "python-dotenv",
    "rich",           # Already have for text agent
    "click",          # CLI framework
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

### Core Code: `purger.py`

```python
"""Safe history purging logic."""
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple
from collections import OrderedDict
from .models import HistoryEntry
from .rules import should_remove

class SafePurger:
    """Safely purge history with multiple safety nets."""
    
    def __init__(self, history_file: Path = None):
        self.history_file = history_file or Path.home() / '.zsh_history'
        self.purge_log = Path.home() / '.zsh_history_purged.log'
    
    def purge(self, preview: bool = True) -> dict:
        """Purge history with safety checks."""
        
        # 1. Validate history file
        if not self.history_file.exists():
            raise FileNotFoundError(f"History file not found: {self.history_file}")
        
        # 2. Parse history
        from .parser import ZshHistoryParser
        parser = ZshHistoryParser(self.history_file)
        entries = list(parser.parse())
        
        # 3. Decide what to keep/remove
        to_keep, to_remove, reasons = self._decide_purge(entries)
        
        # 4. Show preview
        stats = self._show_preview(entries, to_keep, to_remove)
        
        if preview:
            return stats  # Stop here, don't modify
        
        # 5. Create backup
        backup_path = self._create_backup()
        
        # 6. Write purge log
        self._write_purge_log(to_remove, reasons)
        
        # 7. Atomic write new history
        self._atomic_write_history(to_keep)
        
        # 8. Verify new history is valid
        if not self._validate_history_file():
            self._rollback(backup_path)
            raise Exception("Purge failed, rolled back")
        
        return {
            'kept': len(to_keep),
            'removed': len(to_remove),
            'backup': backup_path,
        }
    
    def _decide_purge(self, entries: List[HistoryEntry]) -> Tuple[List, List, dict]:
        """Decide what to keep and what to remove."""
        to_keep = []
        to_remove = []
        reasons = {}
        
        # Track seen commands for duplicate detection
        seen = OrderedDict()  # Preserve order
        
        # Cutoff for recent commands (last 7 days)
        cutoff = datetime.now() - timedelta(days=7)
        
        for entry in entries:
            # Always keep recent commands
            if entry.timestamp and entry.timestamp > cutoff:
                to_keep.append(entry)
                seen[entry.command] = entry
                continue
            
            # Check if should remove
            should_remove_flag, reason = should_remove(entry, seen)
            
            if should_remove_flag:
                to_remove.append(entry)
                reasons[entry.command] = reason
            else:
                to_keep.append(entry)
                # Track as seen (for duplicate detection)
                if entry.command not in seen:
                    seen[entry.command] = entry
        
        return to_keep, to_remove, reasons
    
    def _create_backup(self) -> Path:
        """Create timestamped backup."""
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        backup_file = self.history_file.parent / f'.zsh_history.backup.{timestamp}'
        shutil.copy2(self.history_file, backup_file)
        
        # Keep last 10 backups, remove older
        self._cleanup_old_backups(keep=10)
        
        return backup_file
    
    def _atomic_write_history(self, entries: List[HistoryEntry]):
        """Write new history atomically."""
        import os
        temp_file = self.history_file.parent / f'.zsh_history.tmp.{os.getpid()}'
        
        try:
            with open(temp_file, 'w') as f:
                for entry in entries:
                    f.write(entry.to_zsh_format() + '\n')
            
            # Atomic rename
            temp_file.rename(self.history_file)
        except Exception as e:
            temp_file.unlink(missing_ok=True)
            raise Exception(f"Failed to write history: {e}")
    
    def _write_purge_log(self, removed: List[HistoryEntry], reasons: dict):
        """Log what was removed."""
        with open(self.purge_log, 'a') as f:
            f.write(f"\n# Purge: {datetime.now()}\n")
            f.write(f"# Removed: {len(removed)} commands\n\n")
            
            for entry in removed:
                reason = reasons.get(entry.command, "unknown")
                f.write(f"# Reason: {reason}\n")
                f.write(f"{entry.command}\n")
    
    def _show_preview(self, total, to_keep, to_remove) -> dict:
        """Show what would be removed."""
        from rich.console import Console
        from rich.table import Table
        
        console = Console()
        
        stats = {
            'total': len(total),
            'kept': len(to_keep),
            'removed': len(to_remove),
            'pct_removed': len(to_remove) / len(total) * 100,
        }
        
        table = Table(title="Purge Preview")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="magenta")
        
        table.add_row("Total commands", f"{stats['total']:,}")
        table.add_row("Will keep", f"{stats['kept']:,}")
        table.add_row("Will remove", f"{stats['removed']:,}")
        table.add_row("% removed", f"{stats['pct_removed']:.1f}%")
        
        console.print(table)
        
        return stats
    
    def restore_backup(self, backup_file: Path = None):
        """Restore from backup."""
        if backup_file is None:
            backup_file = self._find_latest_backup()
        
        shutil.copy2(backup_file, self.history_file)
        return backup_file
```

### Core Code: `rules.py`

```python
"""Purge rules - what to remove and what to keep."""
from typing import Tuple
from .models import HistoryEntry

# Simple noise commands
NOISE_COMMANDS = {
    'ls', 'ls -la', 'ls -l', 'll', 'ls -lah',
    'cd', 'cd ..', 'cd -', 'cd ~',
    'pwd',
    'clear', 'cls',
    'exit', 'logout',
    'history', 'history | grep',
}

# Indicators of complex/important commands
COMPLEXITY_INDICATORS = ['|', '&&', '||', ';', '$(', '`', '>', '>>', '<', '<<']

def should_remove(entry: HistoryEntry, seen: dict) -> Tuple[bool, str]:
    """
    Determine if command should be removed.
    
    Args:
        entry: History entry to check
        seen: Dict of already seen commands
    
    Returns:
        (should_remove: bool, reason: str)
    """
    command = entry.command.strip()
    
    # Rule 1: Simple noise commands
    if command in NOISE_COMMANDS:
        return True, "simple_noise"
    
    # Rule 2: Exact duplicate (already seen)
    if command in seen:
        return True, "exact_duplicate"
    
    # Rule 3: Failed command that we've seen succeed
    if entry.exit_code and entry.exit_code != 0:
        if command in seen and seen[command].exit_code == 0:
            return True, "failed_duplicate"
    
    # Rule 4: Complex commands always keep
    if any(indicator in command for indicator in COMPLEXITY_INDICATORS):
        return False, "complex_command"
    
    # Rule 5: Commands with multiple flags - keep
    flag_count = command.count(' -') + command.count(' --')
    if flag_count >= 2:
        return False, "multiple_flags"
    
    # Rule 6: Long commands - keep
    if len(command) > 50:
        return False, "long_command"
    
    # Default: keep it
    return False, "default_keep"
```

### Entry Point: `commands.py`

```python
"""CLI commands for history curator."""
import click
from rich.console import Console
from pathlib import Path
from .purger import SafePurger

console = Console()

@click.group(name='shell')
def shell_group():
    """Shell history management commands"""
    pass

@shell_group.command()
@click.option('--preview/--no-preview', default=True, 
              help='Preview changes without modifying history')
@click.option('--history-file', type=Path, help='Path to zsh history file')
def purge(preview, history_file):
    """
    Purge noise and duplicates from shell history.
    
    By default, shows a preview without making changes.
    Use --no-preview to actually modify history.
    """
    
    if preview:
        console.print("🔍 Preview mode - no changes will be made", style="bold blue")
    else:
        console.print("⚠️  Will modify history file!", style="bold yellow")
    
    # Initialize purger
    purger = SafePurger(history_file)
    
    # Run purge
    try:
        result = purger.purge(preview=preview)
        
        if preview:
            console.print("\n💡 To actually purge, run:", style="bold")
            console.print("   ab shell purge --no-preview", style="cyan")
        else:
            console.print("\n✅ Purge complete!", style="bold green")
            console.print(f"   Kept: {result['kept']:,} commands")
            console.print(f"   Removed: {result['removed']:,} commands")
            console.print(f"   Backup: {result['backup']}")
            console.print(f"\n💡 To restore: ab shell restore", style="yellow")
    
    except Exception as e:
        console.print(f"\n❌ Error: {e}", style="bold red")
        raise

@shell_group.command()
@click.option('--backup-file', type=Path, help='Specific backup to restore')
def restore(backup_file):
    """Restore history from backup."""
    
    purger = SafePurger()
    
    try:
        restored_file = purger.restore_backup(backup_file)
        console.print(f"✅ Restored from: {restored_file}", style="bold green")
    except Exception as e:
        console.print(f"❌ Error: {e}", style="bold red")
        raise

@shell_group.command()
def backups():
    """List available backups."""
    
    backup_dir = Path.home()
    backups = sorted(backup_dir.glob('.zsh_history.backup.*'), reverse=True)
    
    if not backups:
        console.print("No backups found", style="yellow")
        return
    
    console.print("\n📦 Available backups:", style="bold")
    for i, backup in enumerate(backups[:10], 1):
        size = backup.stat().st_size / 1024  # KB
        console.print(f"  {i}. {backup.name} ({size:.1f} KB)")
    
    if len(backups) > 10:
        console.print(f"\n  ... and {len(backups) - 10} more")
```

## Setup Steps

1. **Add shell agent to existing agent-box** (already have Python structure)

2. **Run preview**:
   ```bash
   ab shell purge --preview
   
   # Output:
   # 🔍 Preview mode - no changes will be made
   # 
   # ┌─────────────────┬────────┐
   # │ Metric          │ Count  │
   # ├─────────────────┼────────┤
   # │ Total commands  │ 10,000 │
   # │ Will keep       │ 2,500  │
   # │ Will remove     │ 7,500  │
   # │ % removed       │ 75.0%  │
   # └─────────────────┴────────┘
   ```

3. **Actually purge**:
   ```bash
   ab shell purge --no-preview
   
   # Output:
   # ⚠️  Will modify history file!
   # ✅ Purge complete!
   #    Kept: 2,500 commands
   #    Removed: 7,500 commands
   #    Backup: ~/.zsh_history.backup.2026-02-06_14-23-45
   ```

4. **If something goes wrong**:
   ```bash
   # Restore from latest backup
   ab shell restore
   
   # Or restore specific backup
   ab shell restore --backup-file ~/.zsh_history.backup.2026-02-06_14-23-45
   ```

5. **Optional: Schedule monthly purge**:
   ```bash
   # Add to crontab
   crontab -e
   
   # Run first Sunday of month at 10 AM (with auto-confirm)
   0 10 1-7 * 0 [ "$(date +\%u)" = 7 ] && /path/to/ab shell purge --no-preview
   ```

## Usage Examples

```bash
# Preview what would be removed (safe, no changes)
ab shell purge

# Same as above (explicit)
ab shell purge --preview

# Actually purge (modifies history)
ab shell purge --no-preview

# Restore from latest backup
ab shell restore

# List available backups
ab shell backups

# Restore specific backup
ab shell restore --backup-file ~/.zsh_history.backup.2026-02-06_14-23-45

# Check purge log
cat ~/.zsh_history_purged.log

# Use custom history file
ab shell purge --history-file ~/.zsh_history.bak
```

## Comparison to Existing Tools

| Feature | This Solution | `history \| grep` | McFly | Atuin |
|---------|---------------|-------------------|-------|-------|
| Remove duplicates | Yes | No | No | No |
| Remove noise | Yes | No | No | No |
| Modifies history | Yes (safely) | No | No | No |
| Backups | Yes (automatic) | Manual | No | No |
| Cloud sync | No | No | No | Optional |
| Local-only | Yes | Yes | Yes | Optional |
| Simple CLI | Yes | Yes | No | No |

**Best for**: Users who want a cleaner history file without clutter, with strong safety guarantees.

## Estimated Development Time

- Project structure (integrate into agent-box): 30 minutes
- History parser: 1 hour
- Purge rules: 1 hour
- Safe purger (backups, atomic writes): 2 hours
- CLI commands: 1 hour
- Testing: 2 hours
- **Total**: ~7-8 hours

## Future Enhancements

1. **Smart Pattern Detection**: Detect `kubectl get pod <X>` patterns and keep only unique examples
2. **Interactive Mode**: Use fzf to review commands before removal
3. **Statistics**: Show command usage trends over time
4. **Auto-alias Suggestions**: "You ran this 50 times, create an alias?"
5. **Bash Support**: Extend to bash history format

## Why This Approach Works

✅ **Safe**: Multiple backups, atomic writes, easy restore  
✅ **Simple**: One command, no complex arguments  
✅ **Fast**: Rule-based, no LLM needed for basic purging  
✅ **Useful**: Ctrl+R becomes actually useful  
✅ **Reversible**: Can always restore from backup  
✅ **Conservative**: Only removes obvious noise and duplicates  

## Limitations

- Only works with zsh history format (extended history preferred)
- Requires understanding of what "noise" means for your workflow
- First purge removes a lot (can be scary, but safe with backups)
- No cross-machine sync (by design - local only)
- Doesn't handle broken/corrupted history files well
