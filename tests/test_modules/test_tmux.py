"""Tests for tmux module."""

import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path


class TestTmuxInstall:
    """Tests for tmux module install function."""
    
    def test_install_checks_already_installed(self, mock_state_dir):
        """Should skip if already installed and not force."""
        from boxup.state import mark_module_installed
        
        mark_module_installed("tmux")
        
        with patch("boxup.modules.tmux.is_module_installed", return_value=True):
            with patch("boxup.modules.tmux.subprocess.run") as mock_run:
                from boxup.modules import tmux
                result = tmux.install(force=False)
                
                mock_run.assert_not_called()
    
    def test_calls_apt_install_tmux(self, mock_state_dir):
        """Should call apt to install tmux."""
        with patch("boxup.modules.tmux.is_module_installed", return_value=False):
            with patch("boxup.modules.tmux.subprocess.run") as mock_run:
                with patch("boxup.modules.tmux.backup_config") as mock_backup:
                    with patch("os.path.exists", return_value=False):
                        from boxup.modules import tmux
                        try:
                            tmux.install(force=True)
                        except:
                            pass
                        
                        # Check that apt install was called
                        calls = mock_run.call_args_list
                        apt_calls = [c for c in calls if "apt" in str(c)]
                        assert len(apt_calls) > 0


class TestPatchTmuxConf:
    """Tests for .tmux.conf patching functionality."""
    
    def test_creates_tmux_conf_if_not_exists(self, temp_home):
        """Should create .tmux.conf if it doesn't exist."""
        tmux_conf_path = temp_home / ".tmux.conf"
        
        from boxup.modules.tmux import patch_tmux_conf
        
        patch_tmux_conf()
        
        assert tmux_conf_path.exists()
    
    def test_adds_boxup_markers(self, temp_home):
        """Should add boxup markers to .tmux.conf."""
        tmux_conf_path = temp_home / ".tmux.conf"
        tmux_conf_path.write_text("# existing\n")
        
        from boxup.modules.tmux import patch_tmux_conf, TMUX_MARKER_START, TMUX_MARKER_END
        
        patch_tmux_conf()
        
        content = tmux_conf_path.read_text()
        assert TMUX_MARKER_START in content
        assert TMUX_MARKER_END in content