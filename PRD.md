# PRD: Boxup — Terminal Development Environment Bootstrap

## 1. Concept & Vision

Boxup is a **one-command terminal bootstrap** that transforms a fresh Debian/Ubuntu or WSL2 environment into a fully configured, beautiful, and productive development machine in minutes. It installs and configures the user's preferred shell (Zsh + Oh My Zsh + Powerlevel10k), terminal multiplexer (tmux), system information fetcher (fastfetch), and essential tooling (NVM, Homebrew, Docker). The experience is idempotent, safe to re-run, and backed by automatic backups.

**Core philosophy**: A developer should be productive in their terminal from minute one, with zero manual configuration after running a single command.

## 2. Design Language

Not applicable — this is a CLI bootstrap tool, not a GUI product.

## 3. Layout & Structure

### Installation Flow
```
install.sh (bash bootstrap)
    └── python3 -m boxup (Python runtime)
            └── Modules executed in dependency order:
                base → brew → zsh → tmux → fastfetch → nvm → apps
```

### State Persistence
- **Location**: `~/.config/boxup/state.json`
- **Purpose**: Track installed modules, versions, and configuration state for idempotency

### Backup Strategy
- **Location**: `~/.config/boxup/backups/{timestamp}/`
- **Trigger**: Before overwriting any existing config file
- **Format**: Timestamped directories containing original configs

### Config Deployment
- User's existing configs (`.zshrc`, `.tmux.conf`, `.p10k.zsh`, fastfetch config) serve as **templates**
- Boxup copies these to `~/.config/boxup/configs/` as baselines
- Modules may patch or replace configs during installation

## 4. Features & Interactions

### Core Features

| Feature | Description |
|---------|-------------|
| **Base System** | Installs git, curl, wget, build-essential via apt |
| **Homebrew** | Installs Homebrew Linux for extended package management |
| **Zsh Setup** | Installs Zsh, Oh My Zsh, Powerlevel10k, fzf, zsh-autosuggestions, zsh-autocomplete |
| **Tmux Setup** | Installs tmux, TPM (plugin manager), tmux-cpu |
| **Fastfetch** | Installs fastfetch with user's custom logo + 42-module config |
| **NVM** | Installs Node Version Manager for Node.js management |
| **Apps** | Docker CE, VSCode (if GUI detected), Opencode CLI |
| **Uninstall** | Complete removal of boxup-installed components, restoring original state |

### GUI Detection
Boxup detects graphical environments to conditionally install VSCode:

| Signal | Environment | VSCode? |
|--------|-------------|---------|
| `WAYLAND_DISPLAY` set | WSLg (Windows Subsystem Linux Graphics) | ✅ Install |
| `DISPLAY` set | X11 forwarded | ✅ Install |
| Desktop environment detected (GNOME, KDE, etc.) | Full GUI desktop | ✅ Install |
| None of above | Headless/server | ❌ Skip |

### Module Dependency Order
```
base → brew → zsh → tmux → fastfetch → nvm → apps
```

### CLI Interface
```bash
python -m boxup           # Run all modules
python -m boxup --dry-run # Preview changes without applying
python -m boxup zsh tmux  # Run specific modules only
python -m boxup --help    # Show help
python -m boxup --uninstall    # Remove all boxup-installed components
```

### Error Handling
- Each module runs independently — one failure does not cascade
- Failed modules are logged with error details
- Final summary shows: succeeded, skipped, failed
- Idempotent: safe to re-run after failures

## 5. Component Inventory

### install.sh (Bootstrap)
- **Role**: Bash entry point — ensures python3 is installed, then delegates to Python
- **Responsibilities**:
  - Detect if python3 exists, install if missing
  - Verify minimum Python version (3.10+)
  - Call `python3 -m boxup`

### Python Package: `boxup/`

| File | Role |
|------|------|
| `__main__.py` | Entry point for `python -m boxup` |
| `cli.py` | Argument parsing (argparse) |
| `system.py` | OS detection, package manager detection |
| `backup.py` | Backup existing configs before overwrite |
| `modules/base.py` | Base apt packages |
| `modules/brew.py` | Homebrew installation |
| `modules/zsh.py` | Zsh + Oh My Zsh + Powerlevel10k + plugins |
| `modules/tmux.py` | tmux + TPM + tmux-cpu |
| `modules/fastfetch.py` | fastfetch installation + config |
| `modules/nvm.py` | NVM installation |
| `modules/apps.py` | Docker, VSCode (if GUI), Opencode |
| `configs/` | Template configs (user's current configs as base) |
| `utils/colors.py` | ANSI color codes for colored output |
| `utils/logger.py` | Structured logging (info/success/warn/error) |

## 6. Technical Approach

### Technology Stack
- **Bootstrap**: Bash (install.sh) — minimal, runs before Python exists
- **Runtime**: Python 3.10+ — all installation logic
- **Dependency Management**: Poetry (dev), pip install -e . (production bootstrap)
- **State**: JSON file at `~/.config/boxup/state.json`

### Package Management
- **apt**: Base system packages
- **Homebrew**: Extended package ecosystem
- **NVM**: Node.js version management
- **Direct download**: fastfetch (no apt package), Opencode (direct binary)

### Target Environments
- Debian 12+
- Ubuntu 22.04+
- WSL2 (Ubuntu on Windows)

## 7. Non-Functional Requirements

| Requirement | Description |
|-------------|-------------|
| **Python 3.10+** | Only runtime dependency beyond bash/curl/git |
| **Colored output** | Clear status indicators (info/success/warn/error) |
| **Idempotent** | Safe to re-run without side effects |
| **Backup before overwrite** | All existing configs archived with timestamp |
| **Graceful failure** | Errors don't cascade; summary at end |
| **Reproducible** | Same result on every run |

## 8. Out of Scope

- Windows native (non-WSL2)
- macOS
- RPM-based distros (Fedora, CentOS)
- Headless server optimization beyond skipping VSCode
- Automatic updates / self-upgrade
- Config rollback (only manual via backup restore)
