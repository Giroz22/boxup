"""Tests for zsh module."""

import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path


class TestZshInstall:
    """Tests for zsh module install function."""
    
    def test_install_checks_already_installed(self, mock_state_dir):
        """Should skip if already installed and not force."""
        from boxup.state import mark_module_installed
        
        mark_module_installed("zsh")
        
        # Should return early without trying to install
        with patch("boxup.modules.zsh.is_module_installed", return_value=True):
            with patch("boxup.modules.zsh.subprocess.run") as mock_run:
                from boxup.modules import zsh
                result = zsh.install(force=False)
                
                # Should not have run any commands
                mock_run.assert_not_called()
    
    def test_calls_apt_install_zsh(self, mock_state_dir):
        """Should call apt to install zsh."""
        with patch("boxup.modules.zsh.is_module_installed", return_value=False):
            with patch("boxup.modules.zsh.subprocess.run") as mock_run:
                with patch("boxup.modules.zsh.backup_config") as mock_backup:
                    with patch("os.path.exists", return_value=False):
                        from boxup.modules import zsh
                        try:
                            zsh.install(force=True)
                        except:
                            pass  # May fail on other steps, we just care about the apt call
                        
                        # Check that apt install was called
                        calls = mock_run.call_args_list
                        apt_calls = [c for c in calls if "apt" in str(c)]
                        assert len(apt_calls) > 0


class TestPatchZshrc:
    """Tests for .zshrc patching functionality."""
    
    def test_creates_zshrc_if_not_exists(self, temp_home):
        """Should create .zshrc if it doesn't exist."""
        zshrc_path = temp_home / ".zshrc"
        
        from boxup.modules.zsh import patch_zshrc
        
        patch_zshrc()
        
        assert zshrc_path.exists()
    
    def test_adds_boxup_markers(self, temp_home):
        """Should add boxup markers to .zshrc."""
        zshrc_path = temp_home / ".zshrc"
        zshrc_path.write_text("# existing content\n")
        
        from boxup.modules.zsh import patch_zshrc, ZSH_MARKER_START, ZSH_MARKER_END
        
        patch_zshrc()
        
        content = zshrc_path.read_text()
        assert ZSH_MARKER_START in content
        assert ZSH_MARKER_END in content