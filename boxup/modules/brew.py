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

    # Check if already installed (try both locations)
    brew_paths = [
        os.path.expanduser("~/.linuxbrew/bin/brew"),
        os.path.expanduser("~/.brew/bin/brew"),
    ]
    if any(os.path.exists(p) for p in brew_paths):
        if not force:
            warn(f"{module_name}: already installed, skipping")
            return True

    if is_module_installed(module_name) and not force:
        warn(f"{module_name}: already installed, skipping")
        return True

    # Refuse to run as root - Homebrew explicitly forbids this
    if os.geteuid() == 0:
        warn(f"{module_name}: Homebrew refuses to install as root")
        warn(f"{module_name}: skipping (run as regular user)")
        return False

    info("Installing Homebrew...")

    try:
        # Run Homebrew installer with proper environment
        env = os.environ.copy()
        env["NONINTERACTIVE"] = "1"
        env["HOMEBREW_NO_ENV_FILTERING"] = "1"

        result = subprocess.run(
            ["/bin/bash", "-c",
             f'curl -fsSL {BREW_INSTALL_URL} | HOMEBREW_NO_ENV_FILTERING=1 NONINTERACTIVE=1 bash'],
            capture_output=True,
            text=True,
            timeout=300,
            env=env,
        )

        if result.returncode != 0:
            # Homebrew sometimes fails silently, check if it actually installed
            if any(os.path.exists(p) for p in brew_paths):
                success(f"{module_name}: installed successfully")
                mark_module_installed(module_name)
                return True
            error(f"Homebrew installation failed: {result.stderr[-500:]}")
            return False

        # Verify installation
        brew_path = os.path.expanduser("~/.linuxbrew/bin/brew")
        if not os.path.exists(brew_path):
            # Try alternative location
            brew_path = os.path.expanduser("~/.brew/bin/brew")
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