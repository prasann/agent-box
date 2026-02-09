"""CLI commands for history curator."""
import click
from rich.console import Console
from pathlib import Path
from .purger import SafePurger


console = Console()


@click.group(name='shell')
def shell_group():
    """Shell history management commands."""
    pass


@shell_group.command()
@click.option('--preview/--no-preview', default=True, 
              help='Preview changes without modifying history (default: preview)')
@click.option('--history-file', type=click.Path(exists=True, path_type=Path), 
              help='Path to zsh history file (default: ~/.zsh_history)')
def purge(preview, history_file):
    """
    Purge noise and duplicates from shell history.
    
    By default, shows a preview without making changes.
    Use --no-preview to actually modify history.
    
    Safety features:
    - Automatic timestamped backup before changes
    - Preview mode by default
    - Keeps recent commands (last 7 days) untouched
    - Atomic writes (all-or-nothing)
    - Easy restore with 'agb shell restore'
    
    Examples:
        agb shell purge              # Preview what would be removed
        agb shell purge --no-preview # Actually purge history
    """
    if preview:
        console.print("🔍 Preview mode - no changes will be made\n", style="bold blue")
    else:
        console.print("⚠️  Will modify history file!\n", style="bold yellow")
    
    # Initialize purger
    purger = SafePurger(history_file)
    
    # Run purge
    try:
        result = purger.purge(preview=preview)
        
        if preview:
            console.print("\n💡 To actually purge, run:", style="bold")
            console.print("   agb shell purge --no-preview", style="cyan")
        else:
            console.print("\n✅ Purge complete!", style="bold green")
            console.print(f"   Kept: {result['kept']:,} commands")
            console.print(f"   Removed: {result['removed']:,} commands")
            if 'backup' in result:
                console.print(f"   Backup: {result['backup']}")
            console.print(f"\n💡 To restore: agb shell restore", style="yellow")
    
    except FileNotFoundError as e:
        console.print(f"\n❌ Error: {e}", style="bold red")
        console.print("\n💡 Tip: Make sure your shell history file exists", style="yellow")
        console.print("   Default location: ~/.zsh_history")
        raise click.Abort()
    except Exception as e:
        console.print(f"\n❌ Error: {e}", style="bold red")
        raise


@shell_group.command()
@click.option('--backup-file', type=click.Path(exists=True, path_type=Path), 
              help='Specific backup to restore (default: latest)')
def restore(backup_file):
    """
    Restore history from backup.
    
    By default, restores from the most recent backup.
    Use --backup-file to restore from a specific backup.
    
    Examples:
        agb shell restore                               # Restore from latest backup
        agb shell restore --backup-file ~/.zsh_history.backup.2026-02-06_14-23-45
    """
    purger = SafePurger()
    
    try:
        restored_file = purger.restore_backup(backup_file)
        console.print(f"✅ Restored from: {restored_file}", style="bold green")
    except FileNotFoundError as e:
        console.print(f"❌ Error: {e}", style="bold red")
        console.print("\n💡 Tip: Check available backups with 'agb shell backups'", style="yellow")
        raise click.Abort()
    except Exception as e:
        console.print(f"❌ Error: {e}", style="bold red")
        raise


@shell_group.command()
def backups():
    """
    List available backups.
    
    Shows up to 10 most recent backups with their sizes.
    
    Example:
        agb shell backups
    """
    purger = SafePurger()
    backups_list = purger.list_backups()
    
    if not backups_list:
        console.print("📦 No backups found", style="yellow")
        console.print("\n💡 Backups are created automatically when you run 'agb shell purge --no-preview'")
        return
    
    console.print("\n📦 Available backups:", style="bold")
    for i, backup in enumerate(backups_list[:10], 1):
        size = backup.stat().st_size / 1024  # KB
        console.print(f"  {i}. {backup.name} ({size:.1f} KB)")
    
    if len(backups_list) > 10:
        console.print(f"\n  ... and {len(backups_list) - 10} more")
    
    console.print(f"\n💡 To restore: agb shell restore --backup-file <path>", style="cyan")
