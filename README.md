# Boxup

Terminal development environment bootstrap for Debian/Ubuntu/WSL2.

## Quick Start

```bash
curl -fsSL https://raw.githubusercontent.com/USER/boxup/main/install.sh | sh
```

Or if Python is already available:

```bash
python -m boxup
```

## Features

- **Base System**: git, curl, wget, build-essential
- **Homebrew**: Linux package manager
- **Zsh**: Oh My Zsh + Powerlevel10k + fzf + zsh-autosuggestions
- **Tmux**: TPM + tmux-cpu
- **Fastfetch**: System info display
- **NVM**: Node.js version manager
- **Apps**: Docker CE, VSCode (GUI only), Opencode CLI, gentle-ai

## Modules

```
base → brew → zsh → tmux → fastfetch → nvm → apps
```

## CLI Options

```bash
python -m boxup           # Run all modules
python -m boxup --dry-run # Preview without applying
python -m boxup zsh tmux  # Run specific modules
python -m boxup -v        # Verbose output
python -m boxup --uninstall # Remove all components
```

## State

State is stored in `~/.config/boxup/state.json`

Backups are stored in `~/.config/boxup/backups/{timestamp}/`