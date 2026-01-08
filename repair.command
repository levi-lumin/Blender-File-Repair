#!/bin/bash

# Blend_Repair - macOS Launcher
# Place your corrupted .blend file in this folder and double-click this script

set -e

# Get script directory (works when double-clicked)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================"
echo "   Blend_Repair - macOS        "
echo "================================"
echo

# Find Python (prefer python3, check Homebrew paths)
PYTHON=""
if command -v python3 &> /dev/null; then
    PYTHON="python3"
elif [ -x "/usr/local/bin/python3" ]; then
    PYTHON="/usr/local/bin/python3"
elif [ -x "/opt/homebrew/bin/python3" ]; then
    PYTHON="/opt/homebrew/bin/python3"
elif command -v python &> /dev/null; then
    PYTHON="python"
fi

if [ -z "$PYTHON" ]; then
    echo "[ERROR] Python not found. Please install Python 3.8+"
    echo "        brew install python3"
    echo "        or download from python.org"
    echo
    echo "Press any key to exit..."
    read -n 1
    exit 1
fi

echo "[INFO] Using Python: $($PYTHON --version)"

# Check/install zstandard
if ! $PYTHON -c "import zstandard" 2>/dev/null; then
    echo "[INFO] Installing required module: zstandard..."
    $PYTHON -m pip install zstandard --user --quiet 2>/dev/null || \
    $PYTHON -m pip install zstandard --quiet 2>/dev/null || \
    echo "[WARN] Could not install zstandard. Compression repair may not work."
fi

# Find .blend files (excluding *_repaired.blend)
BLEND_FILES=()
for f in *.blend; do
    if [[ -f "$f" && ! "$f" =~ _repaired\.blend$ ]]; then
        BLEND_FILES+=("$f")
    fi
done

if [ ${#BLEND_FILES[@]} -eq 0 ]; then
    echo
    echo "[ERROR] No .blend files found in this directory."
    echo "        Place your corrupted .blend file here and run this script again."
    echo
    echo "Press any key to exit..."
    read -n 1
    exit 1
fi

# Process files
for blend_file in "${BLEND_FILES[@]}"; do
    echo
    echo "========================================"
    echo "Processing: $blend_file"
    echo "========================================"
    $PYTHON "$SCRIPT_DIR/repair_blend.py" "$blend_file"
done

echo
echo "Done! Check for *_repaired.blend files."
echo
echo "Press any key to exit..."
read -n 1
