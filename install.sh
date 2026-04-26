#!/usr/bin/env bash
# Boxup - Terminal Development Environment Bootstrap
# Minimal bash bootstrap that ensures python3 is installed

set -e

BOXUP_DIR="${HOME}/.local/boxup"
BOXUP_VENV="${BOXUP_DIR}/venv"
BOXUP_BIN="${BOXUP_DIR}/bin"

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

# Create boxup directory and venv if needed
if [ ! -d "$BOXUP_VENV" ]; then
    echo "[INFO] Creating boxup environment..."
    mkdir -p "$BOXUP_DIR"
    python3 -m venv "$BOXUP_VENV"
fi

# Activate venv and install boxup
echo "[INFO] Installing boxup..."
source "${BOXUP_VENV}/bin/activate"
pip install --upgrade pip -q
pip install -e . -q

# Create wrapper script if not exists or outdated
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
