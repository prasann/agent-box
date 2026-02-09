"""Tests for shell history parser."""
import pytest
from pathlib import Path
from datetime import datetime
from ab.agents.shell.parser import ZshHistoryParser
from ab.agents.shell.models import HistoryEntry


def test_parser_extended_format(tmp_path):
    """Test parsing extended zsh history format."""
    history_file = tmp_path / ".zsh_history"
    history_file.write_text(": 1707217234:2;git status\n")
    
    parser = ZshHistoryParser(history_file)
    entries = list(parser.parse())
    
    assert len(entries) == 1
    assert entries[0].command == "git status"
    assert entries[0].timestamp == datetime.fromtimestamp(1707217234)
    assert entries[0].elapsed_seconds == 2


def test_parser_simple_format(tmp_path):
    """Test parsing simple history format."""
    history_file = tmp_path / ".zsh_history"
    history_file.write_text("ls -la\ngit status\n")
    
    parser = ZshHistoryParser(history_file)
    entries = list(parser.parse())
    
    assert len(entries) == 2
    assert entries[0].command == "ls -la"
    assert entries[0].timestamp is None
    assert entries[1].command == "git status"


def test_parser_mixed_format(tmp_path):
    """Test parsing mixed format history."""
    history_file = tmp_path / ".zsh_history"
    history_file.write_text(
        ": 1707217234:0;ls -la\n"
        "git status\n"
        ": 1707217235:5;docker-compose up\n"
    )
    
    parser = ZshHistoryParser(history_file)
    entries = list(parser.parse())
    
    assert len(entries) == 3
    assert entries[0].command == "ls -la"
    assert entries[0].timestamp is not None
    assert entries[1].command == "git status"
    assert entries[1].timestamp is None
    assert entries[2].command == "docker-compose up"
    assert entries[2].elapsed_seconds == 5


def test_parser_empty_lines(tmp_path):
    """Test parsing with empty lines."""
    history_file = tmp_path / ".zsh_history"
    history_file.write_text(
        ": 1707217234:0;ls\n"
        "\n"
        ": 1707217235:0;pwd\n"
    )
    
    parser = ZshHistoryParser(history_file)
    entries = list(parser.parse())
    
    # Empty lines should be skipped
    assert len(entries) == 2
    assert entries[0].command == "ls"
    assert entries[1].command == "pwd"


def test_parser_file_not_found():
    """Test parsing when file doesn't exist."""
    parser = ZshHistoryParser(Path("/nonexistent/.zsh_history"))
    
    with pytest.raises(FileNotFoundError):
        list(parser.parse())


def test_history_entry_to_zsh_format():
    """Test converting entry back to zsh format."""
    entry = HistoryEntry(
        command="git status",
        timestamp=datetime.fromtimestamp(1707217234),
        elapsed_seconds=2
    )
    
    result = entry.to_zsh_format()
    assert result == ": 1707217234:2;git status"


def test_history_entry_to_zsh_format_simple():
    """Test converting simple entry to zsh format."""
    entry = HistoryEntry(
        command="ls -la",
        timestamp=None,
        elapsed_seconds=None
    )
    
    result = entry.to_zsh_format()
    assert result == "ls -la"
