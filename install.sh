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

# Try to create venv
if ! python3 -m venv "$BOXUP_VENV" 2>/dev/null; then
    echo "[WARN] python3-venv not available, trying pip --user..."
    
    # Check if we can use pip --user
    if python3 -m pip --version &>/dev/null; then
        echo "[INFO] Using pip --user mode..."
        python3 -m pip install --user --upgrade pip -q
        python3 -m pip install --user -e . -q
        
        # Create wrapper script
        WRAPPER="${HOME}/.local/bin/boxup"
        mkdir -p "${HOME}/.local/bin"
        cat > "$WRAPPER" << 'WRAPPER_EOF'
#!/bin/bash
exec python3 -m boxup "$@"
WRAPPER_EOF
        chmod +x "$WRAPPER"
        
        echo "[INFO] Launching boxup..."
        exec "$WRAPPER" "$@"
    else
        echo "[ERR] Neither venv nor pip available."
        echo ""
        echo "To fix, install python3-venv with sudo:"
        echo "    sudo apt install python3-venv"
        echo ""
        echo "Or if pip is missing:"
        echo "    sudo apt install python3-pip"
        exit 1
    fi
fi

# Activate venv and install boxup
echo "[INFO] Installing boxup..."
source "${BOXUP_VENV}/bin/activate"
pip install --upgrade pip -q
pip install -e . -q

# Create wrapper script
WRAPPER="${HOME}/.local/bin/boxup"
mkdir -p "${HOME}/.local/bin"
cat > "$WRAPPER" << 'WRAPPER_EOF'
#!/bin/bash
source "${HOME}/.local/boxup/venv/bin/activate"
exec python3 -m boxup "$@"
WRAPPER_EOF
chmod +x "$WRAPPER"

# Run boxup with the wrapper
echo "[INFO] Launching boxup..."
exec "$WRAPPER" "$@"
