"""Tests for shell history purger."""
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from ab.agents.shell.purger import SafePurger
from ab.agents.shell.models import HistoryEntry


def test_purger_preview_mode(tmp_path):
    """Test purger in preview mode."""
    history_file = tmp_path / ".zsh_history"
    history_file.write_text(
        ": 1707217234:0;git status\n"
        ": 1707217235:0;git status\n"
        ": 1707217236:2;git log\n"
    )
    
    purger = SafePurger(history_file)
    result = purger.purge(preview=True)
    
    assert result['total'] == 3
    assert result['kept'] == 2  # First git status and git log
    assert result['removed'] == 1  # Duplicate git status
    
    # File should not be modified in preview mode
    assert history_file.read_text().count('\n') == 3


def test_purger_actual_purge(tmp_path):
    """Test actual purging."""
    history_file = tmp_path / ".zsh_history"
    history_file.write_text(
        ": 1707217234:0;git log\n"
        ": 1707217235:0;cd ..\n"
        ": 1707217236:2;git status\n"
        ": 1707217237:0;pwd\n"
        ": 1707217238:0;git status\n"
    )
    
    purger = SafePurger(history_file)
    result = purger.purge(preview=False)
    
    assert result['kept'] == 2  # git log, first git status
    assert result['removed'] == 3  # cd, pwd, duplicate git status
    assert 'backup' in result
    
    # Check file was actually modified
    content = history_file.read_text()
    assert "git status" in content
    assert "git log" in content
    assert "cd .." not in content
    assert "pwd" not in content
    
    # Check backup was created
    backup_path = Path(result['backup'])
    assert backup_path.exists()
    assert backup_path.read_text().count('\n') == 5


def test_purger_keeps_recent_commands(tmp_path):
    """Test that recent commands are kept."""
    history_file = tmp_path / ".zsh_history"
    
    # Create history with recent and old commands
    recent_time = int(datetime.now().timestamp())
    old_time = int((datetime.now() - timedelta(days=10)).timestamp())
    
    history_file.write_text(
        f": {old_time}:0;ls\n"  # Old, should be removed (noise)
        f": {recent_time}:0;ls\n"  # Recent, should be kept even though noise
        f": {recent_time}:0;pwd\n"  # Recent, should be kept even though noise
    )
    
    purger = SafePurger(history_file)
    result = purger.purge(preview=False)
    
    # Recent commands should be kept
    assert result['kept'] >= 2
    
    content = history_file.read_text()
    # Should have at least the two recent commands
    assert content.count(str(recent_time)) == 2


def test_purger_empty_history(tmp_path):
    """Test purger with empty history file."""
    history_file = tmp_path / ".zsh_history"
    history_file.write_text("")
    
    purger = SafePurger(history_file)
    result = purger.purge(preview=True)
    
    assert result['total'] == 0
    assert result['kept'] == 0
    assert result['removed'] == 0


def test_purger_restore_backup(tmp_path):
    """Test restoring from backup."""
    history_file = tmp_path / ".zsh_history"
    original_content = ": 1707217234:0;ls\n: 1707217235:2;git status\n"
    history_file.write_text(original_content)
    
    # Create backup
    purger = SafePurger(history_file)
    result = purger.purge(preview=False)
    backup_path = Path(result['backup'])
    
    # Modify history after purge
    history_file.write_text("modified")
    
    # Restore from backup
    restored = purger.restore_backup(backup_path)
    assert restored == backup_path
    
    # Check content is restored
    assert history_file.read_text() == original_content


def test_purger_list_backups(tmp_path):
    """Test listing backups."""
    history_file = tmp_path / ".zsh_history"
    history_file.write_text(": 1707217234:0;git status\n")
    
    purger = SafePurger(history_file)
    
    # Initially no backups
    backups = purger.list_backups()
    initial_count = len(backups)
    
    # Create a backup by purging
    purger.purge(preview=False)
    
    # Should have one more backup
    backups = purger.list_backups()
    assert len(backups) == initial_count + 1


def test_purger_file_not_found():
    """Test purger with non-existent file."""
    purger = SafePurger(Path("/nonexistent/.zsh_history"))
    
    with pytest.raises(FileNotFoundError):
        purger.purge(preview=True)
