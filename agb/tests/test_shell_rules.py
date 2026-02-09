"""Tests for shell history purge rules."""
import pytest
from datetime import datetime
from ab.agents.shell.rules import should_remove, NOISE_COMMANDS
from ab.agents.shell.models import HistoryEntry


def test_noise_commands_removed():
    """Test that noise commands are identified for removal."""
    for cmd in ['ls', 'ls -la', 'cd', 'cd ..', 'pwd', 'clear', 'exit']:
        entry = HistoryEntry(command=cmd)
        should_remove_flag, reason = should_remove(entry, {})
        assert should_remove_flag is True
        assert reason == "simple_noise"


def test_complex_commands_kept():
    """Test that complex commands are kept."""
    complex_commands = [
        "ls | grep test",
        "git status && git pull",
        "docker ps || echo fail",
        "cat file.txt > output.txt",
        "echo $(date)",
    ]
    
    for cmd in complex_commands:
        entry = HistoryEntry(command=cmd)
        should_remove_flag, reason = should_remove(entry, {})
        assert should_remove_flag is False
        assert reason == "complex_command"


def test_duplicate_commands_removed():
    """Test that duplicate commands are removed."""
    seen = {
        "git status": HistoryEntry(command="git status", timestamp=datetime.now())
    }
    
    entry = HistoryEntry(command="git status")
    should_remove_flag, reason = should_remove(entry, seen)
    
    assert should_remove_flag is True
    assert reason == "exact_duplicate"


def test_first_occurrence_kept():
    """Test that first occurrence is kept."""
    entry = HistoryEntry(command="git status")
    should_remove_flag, reason = should_remove(entry, {})
    
    assert should_remove_flag is False


def test_long_commands_kept():
    """Test that long commands are kept."""
    long_cmd = "a" * 51  # 51 characters
    entry = HistoryEntry(command=long_cmd)
    should_remove_flag, reason = should_remove(entry, {})
    
    assert should_remove_flag is False
    assert reason == "long_command"


def test_commands_with_flags_kept():
    """Test that commands with multiple flags are kept."""
    entry = HistoryEntry(command="ls -la -h --color")
    should_remove_flag, reason = should_remove(entry, {})
    
    assert should_remove_flag is False
    assert reason == "multiple_flags"


def test_failed_duplicate_removed():
    """Test that duplicate commands are removed (whether failed or not)."""
    seen = {
        "git push": HistoryEntry(
            command="git push",
            exit_code=0,
            timestamp=datetime.now()
        )
    }
    
    # Failed command that we've seen succeed - still removed as duplicate
    entry = HistoryEntry(command="git push", exit_code=1)
    should_remove_flag, reason = should_remove(entry, seen)
    
    assert should_remove_flag is True
    # The duplicate check happens before failed check, so it's exact_duplicate
    assert reason == "exact_duplicate"


def test_simple_unique_command_kept():
    """Test that simple but unique commands are kept."""
    entry = HistoryEntry(command="git status")
    should_remove_flag, reason = should_remove(entry, {})
    
    assert should_remove_flag is False
    assert reason == "default_keep"
