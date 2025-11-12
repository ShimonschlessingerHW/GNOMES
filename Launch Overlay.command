#!/bin/bash
# Double-clickable launcher for Gnome Bot Overlay
# This file can be double-clicked in Finder to run the overlay

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Activate virtual environment
source venv/bin/activate

# Run the overlay
python3 overlay.py

# Keep terminal open if there's an error
if [ $? -ne 0 ]; then
    echo ""
    echo "Press any key to close..."
    read -n 1
fi

