#!/bin/bash
# Victor LLM One-Click Setup Script for Linux/macOS
# This script creates necessary directories, installs dependencies, and creates a desktop shortcut

set -e  # Exit on error

echo "====================================="
echo "Victor LLM One-Click Setup"
echo "====================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed."
    echo "Please install Python 3.8 or newer using your package manager."
    echo "For Ubuntu/Debian: sudo apt-get install python3 python3-pip"
    echo "For macOS: brew install python3"
    exit 1
fi

echo "[1/5] Python found:"
python3 --version
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create necessary directories
echo "[2/5] Creating necessary directories..."
mkdir -p victor_plugins
mkdir -p bando_persistent
mkdir -p models
echo "Directories created successfully."
echo ""

# Install dependencies
echo "[3/5] Installing Python dependencies..."
echo "This may take a few minutes..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
echo "Dependencies installed successfully."
echo ""

# Create desktop shortcut (Linux with .desktop file)
echo "[4/5] Creating desktop shortcut..."

# Detect desktop directory
if [ -d "$HOME/Desktop" ]; then
    DESKTOP_DIR="$HOME/Desktop"
elif [ -d "$HOME/Escritorio" ]; then
    DESKTOP_DIR="$HOME/Escritorio"
else
    DESKTOP_DIR="$HOME"
    echo "WARNING: Desktop directory not found, creating shortcut in home directory"
fi

DESKTOP_FILE="$DESKTOP_DIR/victor_llm.desktop"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Victor LLM
Comment=Run Victor LLM AI System
Exec=bash "$SCRIPT_DIR/run_victor.sh"
Icon=applications-science
Terminal=true
Categories=Development;Science;
Path=$SCRIPT_DIR
EOF

# Make desktop file executable
chmod +x "$DESKTOP_FILE"

# For some Linux distributions, also try to create in ~/.local/share/applications
LOCAL_APPS_DIR="$HOME/.local/share/applications"
mkdir -p "$LOCAL_APPS_DIR"
cp "$DESKTOP_FILE" "$LOCAL_APPS_DIR/victor_llm.desktop"

echo "Desktop shortcut created successfully!"
echo ""

# Create run script if it doesn't exist
if [ ! -f "run_victor.sh" ]; then
    echo "[5/5] Creating run script..."
    cat > run_victor.sh << 'EOF'
#!/bin/bash
# Victor LLM Run Script

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Starting Victor LLM..."
python3 -m victor_core.main

# Keep terminal open on error
if [ $? -ne 0 ]; then
    echo ""
    echo "Press Enter to exit..."
    read
fi
EOF
    chmod +x run_victor.sh
    echo "Run script created."
else
    echo "[5/5] Run script already exists."
fi
echo ""

echo "====================================="
echo "Setup completed successfully!"
echo "====================================="
echo ""
echo "You can now:"
echo "1. Double-click 'victor_llm.desktop' on your desktop (or in your applications menu)"
echo "2. Run ./run_victor.sh from this directory"
echo "3. Run: python3 -m victor_core.main"
echo ""
echo "Note: Make sure to set your OPENAI_API_KEY environment variable"
echo "if you plan to use OpenAI features."
echo "Example: export OPENAI_API_KEY='your-api-key-here'"
echo ""
