#!/bin/bash

# Blend_Repair - Linux Launcher
# Place your corrupted .blend file in this folder and run this script

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}   Blend_Repair - Linux        ${NC}"
echo -e "${GREEN}================================${NC}"
echo

# Find Python
PYTHON=""
if command -v python3 &> /dev/null; then
    PYTHON="python3"
elif command -v python &> /dev/null; then
    PYTHON="python"
fi

if [ -z "$PYTHON" ]; then
    echo -e "${RED}[ERROR] Python not found. Please install Python 3.8+${NC}"
    echo "        sudo pacman -S python  (Arch)"
    echo "        sudo apt install python3  (Debian/Ubuntu)"
    echo "        sudo dnf install python3  (Fedora)"
    exit 1
fi

echo "[INFO] Using Python: $($PYTHON --version)"

# Check/install zstandard
if ! $PYTHON -c "import zstandard" 2>/dev/null; then
    echo -e "${YELLOW}[INFO] Installing required module: zstandard...${NC}"
    $PYTHON -m pip install zstandard --user --quiet 2>/dev/null || \
    $PYTHON -m pip install zstandard --quiet 2>/dev/null || \
    echo -e "${YELLOW}[WARN] Could not install zstandard. Compression repair may not work.${NC}"
fi

# Find .blend files (excluding *_repaired.blend)
shopt -s nullglob
BLEND_FILES=()
for f in *.blend; do
    if [[ ! "$f" =~ _repaired\.blend$ ]]; then
        BLEND_FILES+=("$f")
    fi
done

if [ ${#BLEND_FILES[@]} -eq 0 ]; then
    echo
    echo -e "${RED}[ERROR] No .blend files found in this directory.${NC}"
    echo "        Place your corrupted .blend file here and run this script again."
    echo
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
echo -e "${GREEN}Done! Check for *_repaired.blend files.${NC}"
