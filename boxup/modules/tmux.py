"""Tmux module - installs tmux with TPM and tmux-cpu."""

import subprocess
import os
from pathlib import Path

from boxup.utils.logger import info, success, warn, error, verbose
from boxup.state import mark_module_installed, is_module_installed
from boxup.backup import backup_config


TMUX_MARKER_START = "# >>> boxup managed >>>"
TMUX_MARKER_END = "# <<< boxup managed <<<"


def install(force: bool = False) -> bool:
    """
    Install and configure tmux with TPM and tmux-cpu.
    
    - Installs tmux via apt
    - Clones TPM (Tmux Plugin Manager)
    - Clones tmux-cpu
    - Patches .tmux.conf with boxup markers
    """
    module_name = "tmux"
    
    if is_module_installed(module_name) and not force:
        warn(f"{module_name}: already installed, skipping")
        return True
    
    info(f"Installing {module_name}...")
    
    try:
        # Install tmux
        subprocess.run(
            ["sudo", "apt", "install", "-y", "tmux"],
            check=True,
            capture_output=True,
        )
        
        # Backup existing .tmux.conf
        backup_config([os.path.expanduser("~/.tmux.conf")])
        
        # Clone TPM
        tpm_dir = os.path.expanduser("~/.tmux/plugins/tpm")
        if not os.path.exists(tpm_dir):
            info("Cloning TPM...")
            Path(tpm_dir).parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                ["git", "clone", "--depth=1",
                 "https://github.com/tmux-plugins/tpm.git",
                 tpm_dir],
                check=True,
                capture_output=True,
            )
        
        # Clone tmux-cpu
        cpu_dir = os.path.expanduser("~/.tmux/plugins/tmux-cpu")
        if not os.path.exists(cpu_dir):
            info("Cloning tmux-cpu...")
            subprocess.run(
                ["git", "clone", "--depth=1",
                 "https://github.com/tmux-plugins/tmux-cpu.git",
                 cpu_dir],
                check=True,
                capture_output=True,
            )
        
        # Patch .tmux.conf with boxup markers
        patch_tmux_conf()
        
        mark_module_installed(module_name)
        success(f"{module_name}: installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        error(f"{module_name}: command failed - {e}")
        return False
    except Exception as e:
        error(f"{module_name}: {e}")
        return False


def patch_tmux_conf() -> None:
    """Patch .tmux.conf with boxup-managed sections."""
    tmux_conf_path = os.path.expanduser("~/.tmux.conf")
    
    # Read existing content
    existing = ""
    if os.path.exists(tmux_conf_path):
        with open(tmux_conf_path, "r") as f:
            existing = f.read()
    
    # Build boxup content
    boxup_content = f"""

{TMUX_MARKER_START}
# Boxup managed section - DO NOT EDIT BETWEEN MARKERS

# Mouse mode
set -g mouse on

# Status bar position
set -g status-position top

# Colors base (matching p10k palette)
set -g status-style "bg=black,fg=white"

# Active window: blue
set -g window-status-current-style "bg=colour4,fg=colour254,bold"
set -g window-status-current-format " #I:#W "

# Inactive windows
set -g window-status-style "bg=black,fg=colour250"
set -g window-status-format " #I:#W "

# Left panel: session name
set -g status-left-style "bg=colour7,fg=colour232,bold"
set -g status-left " #S "

# Right panel: system metrics
set -g status-right-length 80
set -g status-right "#[bg=colour238,fg=colour250] CPU: #{{cpu_percentage}} #[bg=colour4,fg=colour254,bold] RAM: #{{ram_percentage}} "

# Update every 2 seconds
set -g status-interval 2

# Plugins
set -g @plugin 'tmux-plugins/tpm'
set -g @plugin 'tmux-plugins/tmux-cpu'

# Initialize TPM (keep this at the bottom)
run '~/.tmux/plugins/tpm/tpm'

# Pane borders
set -g pane-border-style "fg=colour238"
set -g pane-active-border-style "fg=colour4"

{TMUX_MARKER_END}
"""
    
    # Check if markers already exist, remove old section first
    if TMUX_MARKER_START in existing:
        before = existing.split(TMUX_MARKER_START)[0]
        after = existing.split(TMUX_MARKER_END)[-1] if TMUX_MARKER_END in existing else ""
        new_content = before.strip() + "\n" + boxup_content.strip() + "\n" + after.strip()
    else:
        new_content = existing.strip() + "\n" + boxup_content.strip()
    
    # Write back
    with open(tmux_conf_path, "w") as f:
        f.write(new_content)
    
    verbose("Patched .tmux.conf with boxup markers")