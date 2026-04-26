"""NVM (Node Version Manager) installation module."""

import subprocess
import os
from pathlib import Path

from boxup.utils.logger import info, success, warn, error, verbose
from boxup.state import mark_module_installed, is_module_installed


NVM_INSTALL_URL = "https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh"


def install(force: bool = False) -> bool:
    """
    Install NVM (Node Version Manager).
    
    - Downloads and runs official NVM install script
    - Adds NVM_DIR and loading to .zshrc
    """
    module_name = "nvm"
    
    # Check if nvm is already loaded
    nvm_dir = os.path.expanduser("~/.nvm")
    if os.path.exists(nvm_dir) and not force:
        if is_module_installed(module_name):
            warn(f"{module_name}: already installed, skipping")
            return True
    
    if is_module_installed(module_name) and not force:
        warn(f"{module_name}: already installed, skipping")
        return True
    
    info(f"Installing {module_name}...")
    
    try:
        # Run NVM installer
        result = subprocess.run(
            ["/bin/bash", "-c", f'curl -fsSL {NVM_INSTALL_URL} | bash'],
            capture_output=True,
            text=True,
            timeout=120,
        )
        
        if result.returncode != 0:
            error(f"{module_name}: installation failed - {result.stderr}")
            return False
        
        # Verify installation
        if not os.path.exists(nvm_dir):
            error(f"{module_name}: nvm directory not found after installation")
            return False
        
        # Add NVM to .zshrc via patch
        patch_zshrc_for_nvm()
        
        mark_module_installed(module_name)
        success(f"{module_name}: installed successfully")
        return True
        
    except subprocess.TimeoutExpired:
        error(f"{module_name}: installation timed out")
        return False
    except Exception as e:
        error(f"{module_name}: {e}")
        return False


def patch_zshrc_for_nvm() -> None:
    """Add NVM configuration to .zshrc."""
    zshrc_path = os.path.expanduser("~/.zshrc")
    
    nvm_content = """
# NVM Configuration (boxup managed)
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \\. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \\. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion
"""
    
    if os.path.exists(zshrc_path):
        with open(zshrc_path, "r") as f:
            existing = f.read()
        
        # Only add if not already present
        if 'export NVM_DIR="$HOME/.nvm"' not in existing:
            with open(zshrc_path, "a") as f:
                f.write(nvm_content)
            verbose("Added NVM configuration to .zshrc")
    else:
        with open(zshrc_path, "w") as f:
            f.write(nvm_content)
        verbose("Created .zshrc with NVM configuration")