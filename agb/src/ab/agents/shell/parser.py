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
        """Initialize parser with history file path."""
        self.history_file = history_file or Path.home() / '.zsh_history'
    
    def parse(self) -> Iterator[HistoryEntry]:
        """Parse history file and yield entries."""
        if not self.history_file.exists():
            raise FileNotFoundError(f"History file not found: {self.history_file}")
        
        with open(self.history_file, 'r', errors='replace') as f:
            for line in f:
                line = line.rstrip('\n')
                
                if not line:
                    continue
                
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
