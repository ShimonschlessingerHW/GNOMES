#!/bin/bash
# Run script for the Gnome Bot Overlay

cd "$(dirname "$0")"
source venv/bin/activate
python3 overlay.py

