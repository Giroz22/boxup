"""Uninstall module - removes all boxup-installed components."""

import subprocess
import os
import shutil
from pathlib import Path

from boxup.utils.logger import info, success, warn, error
from boxup.state import load_state, save_state
from boxup.backup import get_latest_backup, restore_from_backup


def uninstall_boxup(restore: bool = False, force: bool = False) -> None:
    """
    Uninstall all boxup-installed components.
    
    Args:
        restore: If True, restore backups after removal
        force: If True, don't ask for confirmation
    """
    if not force:
        confirm = input(
            "This will remove:\n"
            "  - zsh, tmux, fastfetch, docker-ce, code\n"
            "  - Homebrew (~/.linuxbrew)\n"
            "  - NVM (~/.nvm)\n"
            "  - Oh My Zsh, Powerlevel10k, fzf\n"
            "  - Opencode, gentle-ai\n"
            "  - Boxup state (~/.config/boxup)\n\n"
            "Continue? [y/N] "
        )
        if confirm.lower() != "y":
            info("Uninstall cancelled")
            return
    
    info("Starting uninstall...")
    
    # Remove installed packages
    remove_packages()
    
    # Remove Homebrew
    remove_homebrew()
    
    # Remove NVM
    remove_nvm()
    
    # Remove Oh My Zsh and plugins
    remove_oh_my_zsh()
    
    # Remove TPM and tmux plugins
    remove_tmux_plugins()
    
    # Remove opencode and gentle-ai
    remove_binaries()
    
    # Restore backups if requested
    if restore:
        restore_backups()
    
    # Clear boxup state
    clear_boxup_state()
    
    success("Uninstall complete!")


def remove_packages() -> None:
    """Remove installed apt packages."""
    packages = [
        "zsh",
        "tmux",
        "docker-ce",
        "docker-ce-cli",
        "containerd.io",
        "docker-buildx-plugin",
        "docker-compose-plugin",
        "code",
    ]
    
    try:
        subprocess.run(
            ["sudo", "apt", "remove", "-y"] + packages,
            check=False,
            capture_output=True,
        )
        info("Removed apt packages")
    except Exception as e:
        warn(f"Failed to remove some packages: {e}")


def remove_homebrew() -> None:
    """Remove Homebrew installation."""
    brew_dir = Path.home() / ".linuxbrew"
    if brew_dir.exists():
        try:
            # Try official uninstaller first
            uninstaller = brew_dir / "uninstall"
            if uninstaller.exists():
                subprocess.run(
                    ["/bin/bash", str(uninstaller)],
                    check=False,
                    capture_output=True,
                )
            else:
                # Manual removal
                shutil.rmtree(brew_dir)
            info("Removed Homebrew")
        except Exception as e:
            warn(f"Failed to remove Homebrew: {e}")


def remove_nvm() -> None:
    """Remove NVM installation."""
    nvm_dir = Path.home() / ".nvm"
    if nvm_dir.exists():
        try:
            shutil.rmtree(nvm_dir)
            info("Removed NVM")
        except Exception as e:
            warn(f"Failed to remove NVM: {e}")


def remove_oh_my_zsh() -> None:
    """Remove Oh My Zsh, Powerlevel10k, and fzf."""
    home = Path.home()
    
    dirs_to_remove = [
        home / ".oh-my-zsh",
        home / ".fzf",
    ]
    
    for dir_path in dirs_to_remove:
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
                info(f"Removed {dir_path.name}")
            except Exception as e:
                warn(f"Failed to remove {dir_path}: {e}")


def remove_tmux_plugins() -> None:
    """Remove TPM and tmux plugins."""
    tpm_dir = Path.home() / ".tmux" / "plugins"
    if tpm_dir.exists():
        try:
            shutil.rmtree(tpm_dir)
            info("Removed TPM and tmux plugins")
        except Exception as e:
            warn(f"Failed to remove TPM: {e}")


def remove_binaries() -> None:
    """Remove opencode and gentle-ai binaries."""
    bin_dir = Path.home() / ".local" / "bin"
    binaries = ["opencode", "gentle-ai"]
    
    for binary in binaries:
        bin_path = bin_dir / binary
        if bin_path.exists():
            try:
                bin_path.unlink()
                info(f"Removed {binary}")
            except Exception as e:
                warn(f"Failed to remove {binary}: {e}")


def restore_backups() -> None:
    """Restore configuration files from latest backup."""
    latest = get_latest_backup()
    if not latest:
        warn("No backups found to restore")
        return
    
    info(f"Restoring from backup: {latest.name}")
    
    files_to_restore = [
        ".zshrc",
        ".tmux.conf",
        ".p10k.zsh",
    ]
    
    try:
        restore_from_backup(latest, files_to_restore)
        success("Backups restored")
    except Exception as e:
        error(f"Failed to restore backups: {e}")


def clear_boxup_state() -> None:
    """Clear boxup state directory."""
    state_dir = Path.home() / ".config" / "boxup"
    if state_dir.exists():
        try:
            shutil.rmtree(state_dir)
            info("Cleared boxup state")
        except Exception as e:
            warn(f"Failed to clear boxup state: {e}")