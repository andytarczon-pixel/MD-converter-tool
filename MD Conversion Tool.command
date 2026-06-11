#!/bin/bash
# Double-click this file in Finder to launch the app.
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "Setting up virtual environment (first run only)..."
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "Checking dependencies..."
pip install -q -r requirements.txt

echo "Launching converter..."
python app.py
