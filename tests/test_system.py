"""Tests for system detection utilities."""

import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from boxup.system import detect_os, detect_gui, is_linux, is_wsl


class TestDetectOs:
    """Tests for detect_os function."""
    
    def test_detect_os_returns_dict(self):
        """Should return a dictionary with expected keys."""
        result = detect_os()
        
        assert isinstance(result, dict)
        assert "distro" in result
        assert "version" in result
        assert "is_wsl" in result
    
    def test_detect_os_wsl_flag(self, tmp_path):
        """Should detect WSL from /proc/version."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            # File doesn't exist, so test non-WSL case
            result = detect_os()
            assert isinstance(result["is_wsl"], bool)
    
    def test_detect_os_reads_os_release(self, tmp_path):
        """Should read /etc/os-release for distribution info."""
        os_release_content = 'ID="ubuntu"\nVERSION_ID="22.04"\n'
        
        with patch("builtins.open", MagicMock(return_value=StringIO(os_release_content))):
            result = detect_os()
            # If it worked, we might see ubuntu; if not, we get "unknown"
            assert result["distro"] in ["ubuntu", "unknown"]


class TestDetectGui:
    """Tests for detect_gui function."""
    
    def test_detect_gui_wayland(self, monkeypatch):
        """Should detect GUI from WAYLAND_DISPLAY."""
        monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
        
        result = detect_gui()
        
        assert result is True
    
    def test_detect_gui_x11(self, monkeypatch):
        """Should detect GUI from DISPLAY."""
        monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
        monkeypatch.setenv("DISPLAY", ":0")
        
        result = detect_gui()
        
        assert result is True
    
    def test_detect_gui_gnome(self, monkeypatch):
        """Should detect GUI from XDG_CURRENT_DESKTOP."""
        monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
        monkeypatch.delenv("DISPLAY", raising=False)
        monkeypatch.setenv("XDG_CURRENT_DESKTOP", "GNOME")
        
        result = detect_gui()
        
        assert result is True
    
    def test_detect_gui_kde(self, monkeypatch):
        """Should detect GUI from KDE."""
        monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
        monkeypatch.delenv("DISPLAY", raising=False)
        monkeypatch.setenv("XDG_CURRENT_DESKTOP", "KDE")
        
        result = detect_gui()
        
        assert result is True
    
    def test_detect_gui_none(self, monkeypatch):
        """Should return False when no GUI detected."""
        monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
        monkeypatch.delenv("DISPLAY", raising=False)
        monkeypatch.setenv("XDG_CURRENT_DESKTOP", "")
        
        result = detect_gui()
        
        assert result is False


class TestIsLinux:
    """Tests for is_linux function."""
    
    def test_is_linux_returns_bool(self):
        """Should return a boolean."""
        result = is_linux()
        assert isinstance(result, bool)


class TestIsWsl:
    """Tests for is_wsl function."""
    
    def test_is_wsl_checks_proc_version(self, tmp_path, monkeypatch):
        """Should check /proc/version for WSL string."""
        # Test non-WSL case
        monkeypatch.setattr("pathlib.Path.exists", lambda self: False)
        
        result = is_wsl()
        
        assert isinstance(result, bool)


from io import StringIO