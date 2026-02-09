"""Safe history purging logic."""
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple, Dict
from collections import OrderedDict
from rich.console import Console
from rich.table import Table
from .models import HistoryEntry
from .rules import should_remove


console = Console()


class SafePurger:
    """Safely purge history with multiple safety nets."""
    
    def __init__(self, history_file: Path = None):
        """Initialize purger with history file path."""
        self.history_file = history_file or Path.home() / '.zsh_history'
        self.purge_log = Path.home() / '.zsh_history_purged.log'
    
    def purge(self, preview: bool = True) -> dict:
        """
        Purge history with safety checks.
        
        Args:
            preview: If True, only show what would be removed
            
        Returns:
            Dictionary with stats about the purge
        """
        # 1. Validate history file
        if not self.history_file.exists():
            raise FileNotFoundError(f"History file not found: {self.history_file}")
        
        # 2. Parse history
        from .parser import ZshHistoryParser
        parser = ZshHistoryParser(self.history_file)
        entries = list(parser.parse())
        
        if not entries:
            console.print("⚠️  History file is empty", style="yellow")
            return {'total': 0, 'kept': 0, 'removed': 0}
        
        # 3. Decide what to keep/remove
        to_keep, to_remove, reasons = self._decide_purge(entries)
        
        # 4. Show preview
        stats = self._show_preview(entries, to_keep, to_remove)
        
        if preview:
            return stats  # Stop here, don't modify
        
        # 5. Create backup
        backup_path = self._create_backup()
        console.print(f"\n📦 Created backup: {backup_path}", style="blue")
        
        # 6. Write purge log
        self._write_purge_log(to_remove, reasons)
        
        # 7. Atomic write new history
        self._atomic_write_history(to_keep)
        
        # 8. Verify new history is valid
        if not self._validate_history_file():
            self._rollback(backup_path)
            raise Exception("Purge failed validation, rolled back")
        
        stats['backup'] = str(backup_path)
        return stats
    
    def _decide_purge(self, entries: List[HistoryEntry]) -> Tuple[List, List, Dict]:
        """
        Decide what to keep and what to remove.
        
        Returns:
            (to_keep, to_remove, reasons)
        """
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
    
    def _cleanup_old_backups(self, keep: int = 10):
        """Remove old backups, keeping only the most recent ones."""
        backup_dir = self.history_file.parent
        backups = sorted(backup_dir.glob('.zsh_history.backup.*'), reverse=True)
        
        # Remove older backups beyond the keep limit
        for old_backup in backups[keep:]:
            old_backup.unlink()
    
    def _atomic_write_history(self, entries: List[HistoryEntry]):
        """Write new history atomically."""
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
    
    def _validate_history_file(self) -> bool:
        """Validate that the history file is readable and non-empty."""
        try:
            if not self.history_file.exists():
                return False
            
            # Try to read it
            with open(self.history_file, 'r') as f:
                content = f.read()
                return len(content) > 0
        except Exception:
            return False
    
    def _rollback(self, backup_path: Path):
        """Rollback to backup if something went wrong."""
        console.print(f"⚠️  Rolling back to: {backup_path}", style="yellow")
        shutil.copy2(backup_path, self.history_file)
    
    def _write_purge_log(self, removed: List[HistoryEntry], reasons: Dict[str, str]):
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
        stats = {
            'total': len(total),
            'kept': len(to_keep),
            'removed': len(to_remove),
            'pct_removed': (len(to_remove) / len(total) * 100) if len(total) > 0 else 0,
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
    
    def restore_backup(self, backup_file: Path = None) -> Path:
        """
        Restore from backup.
        
        Args:
            backup_file: Specific backup to restore, or None for latest
            
        Returns:
            Path to the backup file that was restored
        """
        if backup_file is None:
            backup_file = self._find_latest_backup()
        
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
        
        shutil.copy2(backup_file, self.history_file)
        return backup_file
    
    def _find_latest_backup(self) -> Path:
        """Find the most recent backup file."""
        backup_dir = self.history_file.parent
        backups = sorted(backup_dir.glob('.zsh_history.backup.*'), reverse=True)
        
        if not backups:
            raise FileNotFoundError("No backup files found")
        
        return backups[0]
    
    def list_backups(self) -> List[Path]:
        """List all available backup files."""
        backup_dir = self.history_file.parent
        return sorted(backup_dir.glob('.zsh_history.backup.*'), reverse=True)
