"""Tests for state management."""

import json
import pytest
from pathlib import Path

from boxup.state import (
    load_state,
    save_state,
    is_module_installed,
    mark_module_installed,
    mark_module_failed,
    reset_module,
    get_module_state,
)


class TestLoadState:
    """Tests for load_state function."""
    
    def test_returns_default_state_when_no_file(self, mock_state_dir):
        """Should return default state when state file doesn't exist."""
        state = load_state()
        
        assert state["version"] == "1.0.0"
        assert state["modules"] == {}
    
    def test_loads_existing_state_file(self, mock_state_dir, sample_state):
        """Should load existing state from file."""
        state_file = mock_state_dir / "state.json"
        state_file.write_text(json.dumps(sample_state))
        
        state = load_state()
        
        assert state["version"] == "1.0.0"
        assert "base" in state["modules"]


class TestSaveState:
    """Tests for save_state function."""
    
    def test_saves_state_to_file(self, mock_state_dir):
        """Should save state to state.json."""
        state = {"version": "1.0.0", "modules": {}}
        
        save_state(state)
        
        state_file = mock_state_dir / "state.json"
        assert state_file.exists()
        
        loaded = json.loads(state_file.read_text())
        assert loaded["version"] == "1.0.0"
    
    def test_adds_last_run_timestamp(self, mock_state_dir):
        """Should add last_run timestamp when saving."""
        state = {"version": "1.0.0", "modules": {}}
        
        save_state(state)
        
        loaded = load_state()
        assert loaded["last_run"] is not None


class TestIsModuleInstalled:
    """Tests for is_module_installed function."""
    
    def test_returns_false_when_no_modules(self, mock_state_dir):
        """Should return False when no modules installed."""
        result = is_module_installed("base")
        
        assert result is False
    
    def test_returns_true_when_module_installed(self, mock_state_dir, sample_state):
        """Should return True when module is marked installed."""
        state_file = mock_state_dir / "state.json"
        state_file.write_text(json.dumps(sample_state))
        
        result = is_module_installed("base")
        
        assert result is True
    
    def test_returns_false_for_uninstalled_module(self, mock_state_dir, sample_state):
        """Should return False for module that's not installed."""
        state_file = mock_state_dir / "state.json"
        state_file.write_text(json.dumps(sample_state))
        
        result = is_module_installed("apps")
        
        assert result is False


class TestMarkModuleInstalled:
    """Tests for mark_module_installed function."""
    
    def test_marks_module_as_installed(self, mock_state_dir):
        """Should mark a module as installed."""
        mark_module_installed("base")
        
        state = load_state()
        assert state["modules"]["base"]["installed"] is True
    
    def test_adds_timestamp(self, mock_state_dir):
        """Should add timestamp when marking installed."""
        mark_module_installed("base")
        
        state = load_state()
        assert "timestamp" in state["modules"]["base"]


class TestGetModuleState:
    """Tests for get_module_state function."""
    
    def test_returns_none_for_missing_module(self, mock_state_dir):
        """Should return None for non-existent module."""
        result = get_module_state("nonexistent")
        
        assert result is None
    
    def test_returns_module_state(self, mock_state_dir, sample_state):
        """Should return the state of a specific module."""
        state_file = mock_state_dir / "state.json"
        state_file.write_text(json.dumps(sample_state))
        
        result = get_module_state("base")
        
        assert result["installed"] is True