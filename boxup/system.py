"""OS and GUI detection utilities."""

import os
import platform
from typing import Dict


def detect_os() -> Dict[str, str]:
    """
    Detect operating system and distribution.
    
    Returns:
        dict with keys: distro, version, is_wsl
    """
    result = {
        "distro": "unknown",
        "version": "unknown",
        "is_wsl": False,
    }
    
    # Check for WSL
    if os.path.exists("/proc/sys/fs/binfmt_misc/WSLInterop") or os.path.exists("/etc/wsl.conf"):
        result["is_wsl"] = True
    
    # Read /etc/os-release
    try:
        with open("/etc/os-release", "r") as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith("ID="):
                    result["distro"] = line.split("=")[1].strip().strip('"')
                elif line.startswith("VERSION_ID="):
                    result["version"] = line.split("=")[1].strip().strip('"')
    except FileNotFoundError:
        pass
    
    return result


def detect_gui() -> bool:
    """
    Detect if a graphical environment is available.
    
    Returns:
        True if GUI detected (WSLg, X11, or desktop environment)
    """
    # Check for WSLg (Wayland)
    if os.environ.get("WAYLAND_DISPLAY"):
        return True
    
    # Check for X11
    if os.environ.get("DISPLAY"):
        return True
    
    # Check for desktop environment
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    desktop_envs = ["gnome", "kde", "xfce", "lxde", "mate", "cinnamon", "unity"]
    for env in desktop_envs:
        if env in desktop:
            return True
    
    return False


def is_linux() -> bool:
    """Check if running on Linux."""
    return platform.system() == "Linux"


def is_wsl() -> bool:
    """Check if running on WSL."""
    if os.path.exists("/proc/sys/fs/binfmt_misc/WSLInterop"):
        return True
    try:
        with open("/proc/version", "r") as f:
            return "WSL" in f.read()
    except:
        return False