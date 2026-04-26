"""Base system module - installs essential packages."""

import subprocess
from boxup.utils.logger import info, success, warn, error
from boxup.state import mark_module_installed, is_module_installed


def install(force: bool = False) -> bool:
    """
    Install base system packages via apt.
    
    Packages: git, curl, wget, build-essential, software-properties-common
    """
    module_name = "base"
    
    if is_module_installed(module_name) and not force:
        warn(f"{module_name}: already installed, skipping")
        return True
    
    info("Installing base system packages...")
    
    packages = [
        "git",
        "curl",
        "wget",
        "build-essential",
        "software-properties-common",
    ]
    
    try:
        # Update apt
        subprocess.run(
            ["sudo", "apt", "update"],
            check=True,
            capture_output=True,
        )
        
        # Install packages
        subprocess.run(
            ["sudo", "apt", "install", "-y"] + packages,
            check=True,
            capture_output=True,
        )
        
        mark_module_installed(module_name)
        success(f"{module_name}: installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        error(f"{module_name}: installation failed - {e}")
        return False


def check_installed() -> bool:
    """Check if base packages are installed."""
    try:
        subprocess.run(
            ["git", "--version"],
            check=True,
            capture_output=True,
        )
        return True
    except:
        return False