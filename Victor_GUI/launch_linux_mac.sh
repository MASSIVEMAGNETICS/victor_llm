#!/bin/bash
echo "=============================================="
echo "Victor Prime - Control Panel Launcher (Mac/Linux)"
echo "=============================================="

echo "[1/3] Setting up Python environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

echo "[2/3] Installing/Checking dependencies..."
pip install -r requirements.txt

echo "[3/3] Launching Victor GUI..."
# Attempt to open browser automatically
if which xdg-open > /dev/null
then
  xdg-open http://127.0.0.1:7860 &
elif which open > /dev/null
then
  open http://127.0.0.1:7860 &
fi

python3 app.py
