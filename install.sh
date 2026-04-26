#!/usr/bin/env bash
# Boxup - Terminal Development Environment Bootstrap
# Minimal bash bootstrap that ensures python3 is installed

# IMPORTANT: Do NOT run as root. Boxup will prompt for sudo when needed.
if [ "$EUID" -eq 0 ]; then
    echo "[ERR] Do NOT run boxup as root!"
    echo ""
    echo "Boxup will ask for sudo password when it needs to install"
    echo "system packages (zsh, tmux, docker, etc.)"
    echo ""
    echo "Run without sudo:"
    echo "    ./install.sh"
    exit 1
fi

BOXUP_DIR="${HOME}/.local/boxup"
BOXUP_VENV="${BOXUP_DIR}/venv"
BOXUP_BIN="${BOXUP_VENV}/bin"

echo "[INFO] Boxup bootstrap starting..."

# Check if python3 exists
if ! command -v python3 &> /dev/null; then
    echo "[ERR] Python3 not found. Please install Python 3.10+ first."
    echo "      Ubuntu/Debian: sudo apt install python3"
    exit 1
fi

# Verify python3 version >= 3.10
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo "[ERR] Python 3.10+ required, found $PYTHON_VERSION"
    exit 1
fi

echo "[OK] Python $PYTHON_VERSION detected"

# Remove old venv if it exists and is not working
if [ -d "$BOXUP_VENV" ]; then
    if [ ! -f "${BOXUP_BIN}/pip" ] || [ ! -f "${BOXUP_BIN}/python3" ]; then
        echo "[INFO] Removing corrupted venv..."
        rm -rf "$BOXUP_VENV"
    fi
fi

# Create boxup directory and venv if needed
if [ ! -d "$BOXUP_VENV" ]; then
    echo "[INFO] Creating boxup environment..."
    mkdir -p "$BOXUP_DIR"
    python3 -m venv "$BOXUP_VENV"
fi

# Activate venv and install boxup
echo "[INFO] Installing boxup..."
source "${BOXUP_BIN}/activate"

# Upgrade pip first
"${BOXUP_BIN}/pip" install --upgrade pip

# Install boxup in regular mode (not editable, more reliable)
"${BOXUP_BIN}/pip" install .

# Create wrapper script
WRAPPER="${HOME}/.local/bin/boxup"
mkdir -p "${HOME}/.local/bin"
cat > "$WRAPPER" << 'WRAPPER_EOF'
#!/bin/bash
if [ -f "${HOME}/.local/boxup/venv/bin/activate" ]; then
    source "${HOME}/.local/boxup/venv/bin/activate"
fi
exec python3 -m boxup "$@"
WRAPPER_EOF
chmod +x "$WRAPPER"

# Run boxup with the wrapper
echo "[INFO] Launching boxup..."
exec "$WRAPPER" "$@"
