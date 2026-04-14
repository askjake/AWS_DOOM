#!/bin/bash
# AWS DOOM Launcher Script (Linux/Mac)

echo "========================================"
echo "  AWS DOOM - Architecture Explorer"
echo "========================================"
echo ""

# Check if we're in the right directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found. Please install Python 3.10+"
    exit 1
fi

# Check for pygame
if ! python3 -c "import pygame" 2>/dev/null; then
    echo "pygame not found. Installing..."
    pip install pygame>=2.5.0
fi

# Check for snapshot files
SNAPSHOT_DIR="$HOME/AWS_Architecture_explorer/snapshots"
if [ ! -d "$SNAPSHOT_DIR" ] || [ -z "$(ls -A $SNAPSHOT_DIR/*.json 2>/dev/null)" ]; then
    echo ""
    echo "Warning: No AWS snapshot files found in $SNAPSHOT_DIR"
    echo "Please run the snapshot collector first:"
    echo "  cd ~/AWS_Architecture_explorer"
    echo "  python collect_snapshot.py --region us-west-2 --out snapshots/snapshot.json"
    echo ""
    exit 1
fi

# Run the game
echo "Launching AWS DOOM..."
echo ""
python3 aws_doom.py "$@"
