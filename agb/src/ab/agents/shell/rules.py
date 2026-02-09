"""Purge rules - what to remove and what to keep."""
from typing import Tuple
from .models import HistoryEntry


# Simple noise commands
NOISE_COMMANDS = {
    'ls', 'ls -la', 'ls -l', 'll', 'ls -lah', 'ls -lt', 'ls -ltr',
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
        seen: Dict of already seen commands (command -> entry)
    
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
