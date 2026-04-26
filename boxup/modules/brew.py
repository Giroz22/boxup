"""Homebrew installation module."""

import subprocess
import os
from boxup.utils.logger import info, success, warn, error
from boxup.state import mark_module_installed, is_module_installed


BREW_INSTALL_URL = "https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh"


def install(force: bool = False) -> bool:
    """
    Install Homebrew for Linux.
    
    Adds brew to .zshrc via shellenv evaluation.
    """
    module_name = "brew"
    
    # Check if already installed
    if os.path.exists(os.path.expanduser("~/.linuxbrew/bin/brew")):
        if not force:
            warn(f"{module_name}: already installed, skipping")
            return True
    
    if is_module_installed(module_name) and not force:
        warn(f"{module_name}: already installed, skipping")
        return True
    
    info("Installing Homebrew...")
    
    try:
        # Run Homebrew installer
        result = subprocess.run(
            [
                "/bin/bash",
                "-c",
                f'NONINTERACTIVE=1 curl -fsSL {BREW_INSTALL_URL} | bash'
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )
        
        if result.returncode != 0:
            error(f"Homebrew installation failed: {result.stderr}")
            return False
        
        # Verify installation
        brew_path = os.path.expanduser("~/.linuxbrew/bin/brew")
        if not os.path.exists(brew_path):
            error(f"{module_name}: brew binary not found after installation")
            return False
        
        mark_module_installed(module_name)
        success(f"{module_name}: installed successfully")
        return True
        
    except subprocess.TimeoutExpired:
        error(f"{module_name}: installation timed out")
        return False
    except Exception as e:
        error(f"{module_name}: {e}")
        return False


def get_shellenv() -> str:
    """Get the brew shellenv command."""
    return 'eval "$(~/.linuxbrew/bin/brew shellenv)"'