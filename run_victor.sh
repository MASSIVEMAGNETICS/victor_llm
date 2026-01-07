#!/bin/bash
# Victor LLM Run Script for Linux/macOS
# This script runs the Victor LLM AI System

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "====================================="
echo "Victor LLM AI System"
echo "====================================="
echo ""
echo "Starting Victor Core..."
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed."
    echo "Please run setup.sh first."
    read -p "Press Enter to exit..."
    exit 1
fi

# Run Victor Core
python3 -m victor_core.main

# Keep terminal open on error
if [ $? -ne 0 ]; then
    echo ""
    echo "An error occurred. Check the output above."
    read -p "Press Enter to exit..."
fi
