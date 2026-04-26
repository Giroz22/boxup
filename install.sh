#!/usr/bin/env bash
# Boxup - Terminal Development Environment Bootstrap
# Minimal bash bootstrap that ensures python3 is installed

set -e

echo "[INFO] Boxup bootstrap starting..."

# Check if python3 exists
if ! command -v python3 &> /dev/null; then
    echo "[INFO] Python3 not found, installing..."
    sudo apt update
    sudo apt install -y python3 python3-pip
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

# Install boxup package in development mode
echo "[INFO] Installing boxup..."
python3 -m pip install -e . --quiet

# Run boxup
echo "[INFO] Launching boxup..."
python3 -m boxup "$@"