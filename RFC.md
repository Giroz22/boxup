# RFC: Boxup — Technical Design

## Status

Accepted — implementation ready.

---

## 1. Overview

Boxup is a terminal bootstrap script that installs and configures a personalized development environment on Debian/Ubuntu and WSL2. This RFC describes the technical architecture, design decisions, and implementation approach.

---

## 2. Technology Choices

### 2.1 Python as Primary Runtime

**Decision**: All installation logic is written in Python (3.10+). A minimal Bash `install.sh` bootstrap handles only the case where Python is not yet installed.

**Rationale**:
- Bash is insufficient for complex installation logic (state management, JSON parsing, dependency resolution)
- Python is universally available on Debian/Ubuntu and WSL2 images
- Provides structured error handling, type safety, and testability
- User explicitly confirmed: "install.sh bootstrap en Bash que instala python3 si no existe, todo lo demás en Python"

**Bootstrap Flow**:
```
install.sh
  └── Check python3 exists
  └── If not: apt install python3
  └── Verify python3 >= 3.10
  └── python3 -m boxup
```

### 2.2 Dependency Management

| Environment | Tool |
|-------------|------|
| Development | Poetry |
| Production Bootstrap | `pip install -e .` |

**Rationale**: Poetry provides reproducible dev environments. The `-e` install mode allows the package to be run as `python -m boxup` during bootstrap without publishing to PyPI.

### 2.3 Module Architecture

Each module is a standalone Python subprocess executed via:
```bash
python -m boxup.modules.{name}
```

**Rationale**:
- Modules are isolated — failure in one does not crash the entire bootstrap
- Allows selective execution (`python -m boxup zsh tmux`)
- Each module can be tested independently
- Clear separation of concerns

**Module Execution**: The CLI invokes modules via `subprocess.run()` with explicit error capture.

---

## 3. State Management

### 3.1 State File Location

```
~/.config/boxup/state.json
```

### 3.2 State Schema

```json
{
  "version": "1.0.0",
  "modules": {
    "base": { "installed": true, "timestamp": "ISO8601" },
    "brew": { "installed": true, "timestamp": "ISO8601" },
    "zsh": { "installed": true, "timestamp": "ISO8601", "config_hash": "sha256" },
    "tmux": { "installed": true, "timestamp": "ISO8601", "config_hash": "sha256" },
    "fastfetch": { "installed": true, "timestamp": "ISO8601", "config_hash": "sha256" },
    "nvm": { "installed": true, "timestamp": "ISO8601" },
    "apps": { "installed": true, "timestamp": "ISO8601", "vscode_installed": false }
  },
  "last_run": "ISO8601"
}
```

### 3.3 Idempotency Strategy

- Each module checks `state.json` before installing
- If `module.installed == true` and config hash matches, skip installation
- Force re-install via `--force` flag clears individual module state

---

## 4. Backup Strategy

### 4.1 Backup Location

```
~/.config/boxup/backups/{timestamp}/
```

### 4.2 Backup Trigger

Before modifying any existing config file, boxup:
1. Creates a timestamped backup directory
2. Copies the existing file to the backup
3. Logs the backup path

### 4.3 Files Backed Up

| File | Backup Path |
|------|------------|
| `~/.zshrc` | `~/.config/boxup/backups/{ts}/zshrc` |
| `~/.tmux.conf` | `~/.config/boxup/backups/{ts}/tmux.conf` |
| `~/.p10k.zsh` | `~/.config/boxup/backups/{ts}/p10k.zsh` |
| `~/.config/fastfetch/config.jsonc` | `~/.config/boxup/backups/{ts}/fastfetch_config.jsonc` |

---

## 5. Config Deployment Strategy

### 5.1 Template Source

User's current configs serve as templates:
- `~/.zshrc` (Oh My Zsh + Powerlevel10k + fzf shellenv + nvm + opencode path)
- `~/.tmux.conf` (mouse on, status top, tmux-cpu, TPM)
- `~/.p10k.zsh` (existing Powerlevel10k configuration)
- Fastfetch config (red logo, 42 modules)

### 5.2 Deployment Process

1. Copy user configs to `~/.config/boxup/configs/` as baseline templates
2. During `zsh` module: patch `.zshrc` to add boxup-managed sections (wrapped with markers)
3. During `tmux` module: patch `.tmux.conf` similarly
4. During `fastfetch` module: deploy config to `~/.config/fastfetch/config.jsonc`

### 5.3 Config Markers

Boxup-managed sections in `.zshrc` and `.tmux.conf` are wrapped:
```bash
# >>> boxup managed >>>
# ... managed content ...
# <<< boxup managed <<<
```

On re-run, boxup replaces content between markers rather than appending.

---

## 6. OS Detection

### 6.1 Detection Logic

```python
def detect_os() -> dict:
    # Check /etc/os-release for distribution info
    # Debian 系列: debian, ubuntu, linuxmint, pop
    # WSL detection: /proc/sys/fs/binfmt_misc/WSLInterop or /etc/wsl.conf
    # Return: { "distro": "ubuntu", "version": "22.04", "is_wsl": bool }
```

### 6.2 Supported Distributions

| Distribution | Support Level |
|--------------|---------------|
| Ubuntu 22.04+ | ✅ Full |
| Debian 12+ | ✅ Full |
| WSL2 (Ubuntu) | ✅ Full |
| Pop!_OS | ✅ Full (based on Ubuntu) |
| Linux Mint | ✅ Best effort |

---

## 7. GUI Detection

### 7.1 Detection Logic

```python
def detect_gui() -> bool:
    # Check for WSLg
    if os.environ.get("WAYLAND_DISPLAY"):
        return True

    # Check for X11
    if os.environ.get("DISPLAY"):
        return True

    # Check for desktop environment
    desktop_envs = ["GNOME", "KDE", "XFCE", "LXDE", "MATE", "Cinnamon"]
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    for env in desktop_envs:
        if env.lower() in desktop:
            return True

    return False
```

### 7.2 GUI-Dependent Behavior

| Scenario | VSCode Installed? |
|----------|------------------|
| WSLg (WAYLAND_DISPLAY set) | ✅ Yes |
| X11 forwarded (DISPLAY set) | ✅ Yes |
| GNOME/KDE/XFCE desktop | ✅ Yes |
| Headless/server | ❌ No |

---

## 8. Package Management Strategy

### 8.1 Package Manager Priority

| Package Type | Manager | Reason |
|--------------|---------|--------|
| Base packages (git, curl, etc.) | apt | System package manager |
| Extended packages | Homebrew | User-level package ecosystem |
| Node.js | NVM | Version-specific Node management |
| Development tools (fastfetch) | Direct download | Often newer than apt versions |
| Docker | Docker CE official repo | Up-to-date, official |

### 8.2 Module-Specific Strategies

#### base
- Uses `apt update && apt install`
- Packages: `git`, `curl`, `wget`, `build-essential`, `software-properties-common`

#### brew
- Installs Homebrew Linux via official installer
- Adds to `.zshrc`: `eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"`

#### zsh
- Installs `zsh` via apt
- Installs Oh My Zsh via curl + sh
- Clones Powerlevel10k: `git clone --depth1 https://github.com/romkatv/powerlevel10k`
- Clones plugins: `zsh-autosuggestions`, `zsh-autocomplete`, `fzf`

#### tmux
- Installs `tmux` via apt
- Clones TPM: `git clone https://github.com/tmux-plugins/tpm`
- Clones tmux-cpu: `git clone https://github.com/tmux-plugins/tmux-cpu`

#### fastfetch
- Downloads latest release from GitHub
- Extracts binary to `/usr/local/bin/fastfetch`

#### nvm
- Installs via curl from official install script
- Adds to `.zshrc`: `export NVM_DIR="$HOME/.nvm"`

#### apps
- **Docker CE**: Add Docker repo, `apt install docker-ce`
- **VSCode**: If GUI detected, add Microsoft repo, `apt install code`
- **Opencode**: Download binary from GitHub releases, `chmod +x` to `~/.local/bin/opencode`

---

## 9. Error Handling

### 9.1 Per-Module Error Handling

```python
def run_module(name: str) -> ModuleResult:
    try:
        module = importlib.import_module(f"boxup.modules.{name}")
        module.install()
        update_state(name, success=True)
        return ModuleResult(name=name, status="success")
    except Exception as e:
        log.error(f"Module {name} failed: {e}")
        update_state(name, success=False, error=str(e))
        return ModuleResult(name=name, status="failed", error=str(e))
```

### 9.2 Cascade Prevention

- Each module runs in isolated `subprocess` or `try/except`
- One failure does not affect other modules
- Failed modules are collected for summary

### 9.3 Final Summary

```
=== Boxup Summary ===
✅ base: installed
✅ brew: installed
✅ zsh: installed
⚠️  tmux: skipped (config conflict)
✅ fastfetch: installed
✅ nvm: installed
⚠️  apps: partial (VSCode skipped: headless)

Run again to retry failed modules.
```

---

## 10. Logging Conventions

### 10.1 Log Levels

| Level | Color | Prefix | Usage |
|-------|-------|--------|-------|
| INFO | White | `[INFO]` | General progress |
| SUCCESS | Green | `[OK]` | Successful installation |
| WARN | Yellow | `[WARN]` | Non-critical issues (e.g., config exists) |
| ERROR | Red | `[ERR]` | Failures |

### 10.2 Color Codes (ANSI)

```python
RESET = "\033[0m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
WHITE = "\033[97m"
```

### 10.3 Output Format

```
[OK]   zsh installed successfully
[INFO] configuring .zshrc...
[WARN] .tmux.conf exists, backing up to /home/user/.config/boxup/backups/20260426T120000/
[ERR]  docker installation failed: GPG key error
```

---

## 11. Module Dependency Order

```
base → brew → zsh → tmux → fastfetch → nvm → apps
```

| Order | Module | Dependencies |
|-------|--------|--------------|
| 1 | base | None |
| 2 | brew | base |
| 3 | zsh | base |
| 4 | tmux | base |
| 5 | fastfetch | base |
| 6 | nvm | base |
| 7 | apps | brew, zsh, tmux |

**Rationale**: `base` must run first (provides git, curl, build-essential). `apps` runs last because Docker may depend on Homebrew packages, and VSCode installation benefits from Zsh being configured.

---

## 12. Project Structure

```
boxup/
├── install.sh                    # Bash bootstrap
├── boxup/
│   ├── __main__.py              # Entry: python -m boxup
│   ├── __init__.py
│   ├── cli.py                   # ArgumentParser
│   ├── system.py                # OS/GUI detection
│   ├── backup.py                # Config backup
│   ├── state.py                 # State.json read/write
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── brew.py
│   │   ├── zsh.py
│   │   ├── tmux.py
│   │   ├── fastfetch.py
│   │   ├── nvm.py
│   │   ├── apps.py
│   │   └── uninstall.py
│   ├── configs/
│   │   ├── zshrc.template
│   │   ├── tmux.conf.template
│   │   ├── p10k.zsh.template
│   │   └── fastfetch.jsonc.template
│   └── utils/
│       ├── __init__.py
│       ├── colors.py
│       └── logger.py
├── tests/
│   ├── __init__.py
│   ├── test_system.py
│   ├── test_backup.py
│   ├── test_modules/
│   │   ├── __init__.py
│   │   ├── test_zsh.py
│   │   └── test_tmux.py
│   └── conftest.py
├── pyproject.toml
└── README.md
```

---

## 13. CLI Interface

```bash
# Run all modules (default)
python -m boxup

# Dry run — show what would be done
python -m boxup --dry-run

# Run specific modules only
python -m boxup zsh tmux

# Force re-install a module
python -m boxup --force zsh

# Show verbose output
python -m boxup -v

# Show help
python -m boxup --help

# Uninstall all boxup components
python -m boxup --uninstall

# Uninstall and restore backups
python -m boxup --uninstall --restore

# Uninstall without confirmation
python -m boxup --uninstall --force
```

---

## 14. Arguments Specification

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--dry-run` | flag | False | Preview changes without applying |
| `--force` | flag | False | Re-install even if already installed |
| `-v`, `--verbose` | flag | False | Enable verbose logging |
| `--uninstall` | flag | False | Remove all boxup-installed components |
| `--restore` | flag | False | Restore backups during uninstall |
| `modules` | positional | all | Module names to run |

---

## 16. Environment Variables

| Variable | Purpose |
|----------|---------|
| `BOXUP_STATE_DIR` | Override state directory (default: `~/.config/boxup`) |
| `BOXUP_BACKUP_DIR` | Override backup directory |
| `BOXUP_DRY_RUN` | Equivalent to `--dry-run` |
| `BOXUP_FORCE` | Equivalent to `--force` |
| `WAYLAND_DISPLAY` | WSLg presence (GUI detection) |
| `DISPLAY` | X11 presence (GUI detection) |
| `XDG_CURRENT_DESKTOP` | Desktop environment (GUI detection) |

---

## 17. Security Considerations

- `install.sh` only installs `python3` via apt — no arbitrary curl pipes
- Homebrew installed to `~/.linuxbrew` (user-owned, not system-wide)
- Docker CE installed from official Docker GPG-signed repo
- VSCode installed from Microsoft's official repo
- No credentials or secrets stored in state.json
- Backup files retain original permissions

---

## 17. Rollback Plan

If boxup fails catastrophically:

1. Restore backed-up configs:
   ```bash
   cp ~/.config/boxup/backups/{timestamp}/.zshrc ~/
   cp ~/.config/boxup/backups/{timestamp}/.tmux.conf ~/
   ```

2. Remove installed packages (manual):
   ```bash
   sudo apt remove zsh tmux fastfetch docker-ce
   sudo apt remove brew  # ~/.linuxbrew/uninstall
   ```

3. Remove boxup state:
   ```bash
   rm -rf ~/.config/boxup
   ```

---

## 18. Uninstall Feature

**Decision**: boxup includes a complete uninstall capability that removes all installed components and optionally restores backed-up configs.

### What gets removed

| Component | Remove Method |
|-----------|---------------|
| apt packages | `sudo apt remove zsh tmux fastfetch docker-ce code` |
| Homebrew | `~/.linuxbrew/uninstall` or manual rm |
| NVM | Remove `~/.nvm` directory |
| Oh My Zsh | Remove `~/.oh-my-zsh` |
| Powerlevel10k | Remove `~/.oh-my-zsh/custom/themes/powerlevel10k` |
| tmux plugins (TPM) | Remove `~/.tmux/plugins` |
| fzf | Remove from brew or `~/.fzf` |
| Opencode | `rm ~/.local/bin/opencode` |
| Docker | Remove Docker repo and `docker-ce` |
| Boxup state | `rm -rf ~/.config/boxup` |

### Restore backed configs

- If `--restore` flag: restore configs from most recent backup in `~/.config/boxup/backups/{timestamp}/`
- If no `--restore`: leave system without those configs (user's problem)

### CLI

```bash
python -m boxup --uninstall         # Remove all boxup components
python -m boxup --uninstall --restore  # Remove and restore backups
python -m boxup --uninstall --force     # Don't ask for confirmation
```

### Confirmation prompt

```
This will remove:
  - zsh, tmux, fastfetch, docker-ce, code
  - Homebrew (~/.linuxbrew)
  - NVM (~/.nvm)
  - Oh My Zsh, Powerlevel10k, fzf
  - Boxup state (~/.config/boxup)

 Optionally restore backups? [Y/n]:
```

---

## 19. Future Considerations (Out of Scope)

- Config diff viewer before applying changes
- Interactive mode with confirmation prompts
- Config rollback command (`boxup rollback`)
- Auto-update mechanism
- Multi-machine sync via dotfiles repo
- Support for Fedora/RHEL
- Support for macOS
