"""Fastfetch module - downloads and installs fastfetch binary."""

import subprocess
import os
import shutil
import re
from pathlib import Path

from boxup.utils.logger import info, success, warn, error, verbose
from boxup.state import mark_module_installed, is_module_installed
from boxup.backup import backup_config


def install(force: bool = False) -> bool:
    """
    Download and install fastfetch binary.
    
    - Downloads latest release from GitHub
    - Extracts to /usr/local/bin/fastfetch
    - Deploys user config to ~/.config/fastfetch/config.jsonc
    """
    module_name = "fastfetch"
    
    if is_module_installed(module_name) and not force:
        warn(f"{module_name}: already installed, skipping")
        return True
    
    info(f"Installing {module_name}...")
    
    try:
        # Backup existing fastfetch config
        fastfetch_config = os.path.expanduser("~/.config/fastfetch/config.jsonc")
        backup_config([fastfetch_config])
        
        # Get latest release version
        info("Fetching latest fastfetch release...")
        result = subprocess.run(
            ["curl", "-s", "https://api.github.com/repos/fastfetch-cli/fastfetch/releases/latest"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode != 0:
            error(f"{module_name}: failed to fetch release info")
            return False
        
        # Parse version from JSON
        import json
        try:
            release_info = json.loads(result.stdout)
            version = release_info.get("tag_name", "").lstrip("v")
            assets = release_info.get("assets", [])
        except json.JSONDecodeError:
            error(f"{module_name}: failed to parse release JSON")
            return False
        
        # Find the correct binary for Linux (amd64, x86_64)
        arch = os.uname().machine
        if arch in ["x86_64", "amd64"]:
            arch = "amd64"
        elif arch in ["aarch64", "arm64"]:
            arch = "aarch64"
        else:
            arch = "amd64"  # default
        
        filename = f"fastfetch-linux-{arch}.deb"
        
        download_url = None
        for asset in assets:
            if asset["name"] == filename:
                download_url = asset["browser_download_url"]
                break
        
        if not download_url:
            error(f"{module_name}: could not find {filename} in release assets")
            return False
        
        # Download the package
        info(f"Downloading fastfetch {version}...")
        temp_deb = "/tmp/fastfetch.deb"
        subprocess.run(
            ["curl", "-fsSL", "-o", temp_deb, download_url],
            check=True,
            capture_output=True,
            timeout=120,
        )
        
        # Install the package
        info("Installing fastfetch...")
        subprocess.run(
            ["sudo", "dpkg", "-i", temp_deb],
            check=True,
            capture_output=True,
        )
        
        # Clean up
        os.remove(temp_deb)
        
        # Deploy config
        deploy_config()
        
        mark_module_installed(module_name, version=version)
        success(f"{module_name}: installed successfully (v{version})")
        return True
        
    except subprocess.CalledProcessError as e:
        error(f"{module_name}: command failed - {e}")
        return False
    except Exception as e:
        error(f"{module_name}: {e}")
        return False


def deploy_config() -> None:
    """Deploy fastfetch config to ~/.config/fastfetch/config.jsonc."""
    config_source = Path(__file__).parent.parent / "configs" / "fastfetch.jsonc.template"
    config_target = Path.home() / ".config" / "fastfetch" / "config.jsonc"
    
    # Create config directory
    config_target.parent.mkdir(parents=True, exist_ok=True)
    
    if config_source.exists():
        shutil.copy2(config_source, config_target)
        verbose(f"Deployed fastfetch config to {config_target}")
    else:
        warn(f"Fastfetch config template not found at {config_source}")