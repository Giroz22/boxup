"""Pytest fixtures and configuration."""

import os
import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_home(monkeypatch):
    """Create a temporary home directory for testing."""
    temp_dir = tempfile.mkdtemp()
    
    # Override Path.home() to return temp_dir
    monkeypatch.setattr(Path, "home", lambda: Path(temp_dir))
    
    yield Path(temp_dir)
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_state_dir(temp_home, monkeypatch):
    """Mock state directory path."""
    state_dir = temp_home / ".config" / "boxup"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


@pytest.fixture
def sample_state():
    """Sample state data for testing."""
    return {
        "version": "1.0.0",
        "modules": {
            "base": {"installed": True, "timestamp": "2026-04-26T10:00:00"},
            "brew": {"installed": True, "timestamp": "2026-04-26T10:01:00"},
            "zsh": {"installed": True, "timestamp": "2026-04-26T10:02:00"},
        },
        "last_run": "2026-04-26T10:02:00",
    }


@pytest.fixture
def sample_config_files(temp_home):
    """Create sample config files for testing."""
    configs = {}
    
    # Create .zshrc
    zshrc = temp_home / ".zshrc"
    zshrc.write_text("# Test zshrc content\n")
    configs["zshrc"] = zshrc
    
    # Create .tmux.conf
    tmux_conf = temp_home / ".tmux.conf"
    tmux_conf.write_text("# Test tmux.conf content\n")
    configs["tmux.conf"] = tmux_conf
    
    return configs