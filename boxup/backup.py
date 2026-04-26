"""Backup existing configuration files before modification."""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from boxup.utils.logger import warn, success, info

BACKUP_DIR = Path.home() / ".config" / "boxup" / "backups"


def get_backup_dir() -> Path:
    """Get the backup directory path."""
    return BACKUP_DIR


def create_backup_dir() -> Path:
    """Create a timestamped backup directory."""
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    backup_path = BACKUP_DIR / timestamp
    backup_path.mkdir(parents=True, exist_ok=True)
    return backup_path


def backup_file(file_path: str, backup_base: Optional[Path] = None) -> Optional[Path]:
    """
    Backup a single file if it exists.
    
    Args:
        file_path: Path to the file to backup
        backup_base: Base backup directory (creates timestamped subdir if not provided)
    
    Returns:
        Path to the backup file, or None if file didn't exist
    """
    path = Path(file_path).expanduser()
    
    if not path.exists():
        return None
    
    if backup_base is None:
        backup_base = create_backup_dir()
    
    # Preserve filename, copy to backup dir
    backup_path = backup_base / path.name
    
    shutil.copy2(path, backup_path)
    return backup_path


def backup_config(files: List[str]) -> Dict[str, Optional[Path]]:
    """
    Backup multiple configuration files.
    
    Args:
        files: List of file paths to backup
    
    Returns:
        Dict mapping original paths to backup paths (None if didn't exist)
    """
    backup_base = create_backup_dir()
    results = {}
    
    for file_path in files:
        backup_path = backup_file(file_path, backup_base)
        if backup_path:
            info(f"Backed up {file_path} -> {backup_path}")
            results[file_path] = backup_path
        else:
            results[file_path] = None
    
    return results


def list_backups() -> List[Path]:
    """List all backup directories sorted by newest first."""
    if not BACKUP_DIR.exists():
        return []
    
    backups = sorted(
        [d for d in BACKUP_DIR.iterdir() if d.is_dir()],
        key=lambda d: d.name,
        reverse=True,
    )
    return backups


def get_latest_backup() -> Optional[Path]:
    """Get the most recent backup directory."""
    backups = list_backups()
    return backups[0] if backups else None


def restore_from_backup(backup_dir: Path, files: List[str]) -> None:
    """
    Restore files from a backup directory.
    
    Args:
        backup_dir: Path to the backup directory
        files: List of filenames to restore
    """
    if not backup_dir.exists():
        raise FileNotFoundError(f"Backup directory not found: {backup_dir}")
    
    for filename in files:
        backup_path = backup_dir / filename
        target_path = Path.home() / filename
        
        if backup_path.exists():
            shutil.copy2(backup_path, target_path)
            success(f"Restored {filename} from backup")
        else:
            warn(f"Backup file not found: {backup_path}")