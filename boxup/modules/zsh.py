"""Zsh module - installs Zsh, Oh My Zsh, Powerlevel10k, and plugins."""

import subprocess
import os
import shutil
from pathlib import Path

from boxup.utils.logger import info, success, warn, error, verbose
from boxup.state import mark_module_installed, is_module_installed
from boxup.backup import backup_config


ZSH_MARKER_START = "# >>> boxup managed >>>"
ZSH_MARKER_END = "# <<< boxup managed <<<"


def install(force: bool = False) -> bool:
    """
    Install and configure Zsh with Oh My Zsh, Powerlevel10k, and plugins.
    
    - Installs zsh via apt
    - Installs Oh My Zsh
    - Clones Powerlevel10k theme
    - Clones zsh-autosuggestions, zsh-autocomplete, fzf
    - Patches .zshrc with boxup markers
    """
    module_name = "zsh"
    
    if is_module_installed(module_name) and not force:
        warn(f"{module_name}: already installed, skipping")
        return True
    
    info(f"Installing {module_name}...")
    
    try:
        # Install zsh
        subprocess.run(
            ["sudo", "apt", "install", "-y", "zsh"],
            check=True,
            capture_output=True,
        )
        
        # Backup existing .zshrc
        backup_config([os.path.expanduser("~/.zshrc")])
        
        # Install Oh My Zsh (if not already installed)
        oh_my_zsh_dir = os.path.expanduser("~/.oh-my-zsh")
        if not os.path.exists(oh_my_zsh_dir):
            info("Installing Oh My Zsh...")
            subprocess.run(
                [
                    "/bin/bash", "-c",
                    'sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended'
                ],
                check=True,
                capture_output=True,
                timeout=120,
            )
        
        # Clone Powerlevel10k
        p10k_dir = os.path.expanduser("~/.oh-my-zsh/custom/themes/powerlevel10k")
        if not os.path.exists(p10k_dir):
            info("Cloning Powerlevel10k...")
            subprocess.run(
                ["git", "clone", "--depth=1",
                 "https://github.com/romkatv/powerlevel10k.git",
                 p10k_dir],
                check=True,
                capture_output=True,
            )
        
        # Clone zsh-autosuggestions
        autosuggest_dir = os.path.expanduser("~/.oh-my-zsh/custom/plugins/zsh-autosuggestions")
        if not os.path.exists(autosuggest_dir):
            info("Cloning zsh-autosuggestions...")
            subprocess.run(
                ["git", "clone", "--depth=1",
                 "https://github.com/zsh-users/zsh-autosuggestions.git",
                 autosuggest_dir],
                check=True,
                capture_output=True,
            )
        
        # Clone zsh-autocomplete
        autocomplete_dir = os.path.expanduser("~/.oh-my-zsh/custom/plugins/zsh-autocomplete")
        if not os.path.exists(autocomplete_dir):
            info("Cloning zsh-autocomplete...")
            subprocess.run(
                ["git", "clone", "--depth=1",
                 "https://github.com/marlonrichert/zsh-autocomplete.git",
                 autocomplete_dir],
                check=True,
                capture_output=True,
            )
        
        # Clone fzf (for shell keybindings)
        fzf_dir = os.path.expanduser("~/.fzf")
        if not os.path.exists(fzf_dir):
            info("Cloning fzf...")
            subprocess.run(
                ["git", "clone", "--depth=1",
                 "https://github.com/junegunn/fzf.git",
                 fzf_dir],
                check=True,
                capture_output=True,
                timeout=120,
            )
            # Install fzf
            subprocess.run(
                ["~/.fzf/install", "--all", "--no-bash", "--no-fish"],
                check=True,
                capture_output=True,
                timeout=120,
            )
        
        # Patch .zshrc with boxup markers
        patch_zshrc()
        
        # Copy p10k.zsh template if it doesn't exist
        p10k_source = Path(__file__).parent.parent / "configs" / "p10k.zsh.template"
        p10k_target = os.path.expanduser("~/.p10k.zsh")
        if p10k_source.exists() and not os.path.exists(p10k_target):
            shutil.copy2(p10k_source, p10k_target)
        
        mark_module_installed(module_name)
        success(f"{module_name}: installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        error(f"{module_name}: command failed - {e}")
        return False
    except Exception as e:
        error(f"{module_name}: {e}")
        return False


def patch_zshrc() -> None:
    """Patch .zshrc with boxup-managed sections."""
    zshrc_path = os.path.expanduser("~/.zshrc")
    
    # Read existing content
    existing = ""
    if os.path.exists(zshrc_path):
        with open(zshrc_path, "r") as f:
            existing = f.read()
    
    # Build boxup content
    boxup_content = f"""

{ZSH_MARKER_START}
# Boxup managed section - DO NOT EDIT BETWEEN MARKERS

# Zsh configuration
export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME="powerlevel10k/powerlevel10k"
plugins=(git tmux zsh-autosuggestions)

# Load Oh My Zsh
source $ZSH/oh-my-zsh.sh

# Load zsh-autocomplete
source ~/.oh-my-zsh/custom/plugins/zsh-autocomplete/zsh-autocomplete.plugin.zsh

# zsh-autocomplete keybindings
bindkey '\\r' accept-line
bindkey '^M' accept-line
bindkey '^H' backward-delete-char
bindkey '^?' backward-delete-char

# Powerlevel10k instant prompt
if [[ -r "${{XDG_CACHE_HOME:-$HOME/.cache}}/p10k-instant-prompt-${{(%):-%n}}.zsh" ]]; then
  source "${{XDG_CACHE_HOME:-$HOME/.cache}}/p10k-instant-prompt-${{(%):-%n}}.zsh"
fi

# Load p10k config if exists
[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh

{ZSH_MARKER_END}
"""
    
    # Check if markers already exist, remove old section first
    if ZSH_MARKER_START in existing:
        # Extract content before markers
        before = existing.split(ZSH_MARKER_START)[0]
        # Extract content after markers
        after = existing.split(ZSH_MARKER_END)[-1] if ZSH_MARKER_END in existing else ""
        new_content = before.strip() + "\n" + boxup_content.strip() + "\n" + after.strip()
    else:
        new_content = existing.strip() + "\n" + boxup_content.strip()
    
    # Write back
    with open(zshrc_path, "w") as f:
        f.write(new_content)
    
    verbose("Patched .zshrc with boxup markers")