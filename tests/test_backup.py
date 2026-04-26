"""Tests for backup module."""

import os
import pytest
from pathlib import Path
import shutil

from boxup.backup import (
    backup_file,
    backup_config,
    create_backup_dir,
    list_backups,
    get_latest_backup,
)


class TestCreateBackupDir:
    """Tests for create_backup_dir function."""
    
    def test_creates_backup_directory(self, temp_home):
        """Should create a timestamped backup directory."""
        backup_dir = create_backup_dir()
        
        assert backup_dir.exists()
        assert backup_dir.is_dir()
    
    def test_backup_dir_in_correct_location(self, temp_home):
        """Should create backup dir in ~/.config/boxup/backups/."""
        backup_dir = create_backup_dir()
        
        assert str(backup_dir).startswith(str(temp_home))


class TestBackupFile:
    """Tests for backup_file function."""
    
    def test_backs_up_existing_file(self, temp_home):
        """Should backup an existing file."""
        # Create a test file
        test_file = temp_home / ".zshrc"
        test_file.write_text("test content")
        
        backup_path = backup_file(str(test_file))
        
        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path.read_text() == "test content"
    
    def test_returns_none_for_nonexistent_file(self, temp_home):
        """Should return None if file doesn't exist."""
        backup_path = backup_file(str(temp_home / ".nonexistent"))
        
        assert backup_path is None
    
    def test_preserves_filename(self, temp_home):
        """Should preserve the original filename."""
        test_file = temp_home / ".zshrc"
        test_file.write_text("content")
        
        backup_path = backup_file(str(test_file))
        
        assert backup_path.name == ".zshrc"


class TestBackupConfig:
    """Tests for backup_config function."""
    
    def test_backs_up_multiple_files(self, temp_home):
        """Should backup multiple files."""
        # Create test files
        zshrc = temp_home / ".zshrc"
        zshrc.write_text("zshrc content")
        
        tmux = temp_home / ".tmux.conf"
        tmux.write_text("tmux content")
        
        results = backup_config([str(zshrc), str(tmux)])
        
        assert results[str(zshrc)] is not None
        assert results[str(tmux)] is not None
    
    def test_returns_none_for_missing_files(self, temp_home):
        """Should return None for files that don't exist."""
        results = backup_config([str(temp_home / ".nonexistent")])
        
        assert results[str(temp_home / ".nonexistent")] is None


class TestListBackups:
    """Tests for list_backups function."""
    
    def test_returns_empty_list_when_no_backups(self, temp_home):
        """Should return empty list when no backups exist."""
        backups = list_backups()
        
        assert backups == []


class TestGetLatestBackup:
    """Tests for get_latest_backup function."""
    
    def test_returns_none_when_no_backups(self, temp_home):
        """Should return None when no backups exist."""
        latest = get_latest_backup()
        
        assert latest is None