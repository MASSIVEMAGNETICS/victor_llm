#!/bin/bash
#############################################################
# Victor Prime AGI - One-Click Setup Script (Linux/Mac)
#############################################################

set -e  # Exit on error

echo "=========================================="
echo "  Victor Prime AGI - Setup"
echo "=========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed.${NC}"
    echo "Please install Python 3.8 or newer from https://www.python.org/"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then 
    echo -e "${RED}Error: Python $PYTHON_VERSION is installed, but Python $REQUIRED_VERSION or newer is required.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python $PYTHON_VERSION detected${NC}"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}Virtual environment already exists${NC}"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip --quiet
echo -e "${GREEN}✓ pip upgraded${NC}"
echo ""

# Install dependencies
echo "Installing dependencies..."
echo "This may take a few minutes..."
pip install -r requirements.txt --quiet
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Install package in development mode
echo "Installing Victor Prime AGI in development mode..."
pip install -e . --quiet
echo -e "${GREEN}✓ Victor Prime AGI installed${NC}"
echo ""

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p victor_plugins
mkdir -p victor_bando_persistent
mkdir -p logs
echo -e "${GREEN}✓ Directories created${NC}"
echo ""

echo "=========================================="
echo -e "${GREEN}  Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "To get started:"
echo "  1. Activate the virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Run Victor Prime Core:"
echo "     python -m victor_core.main"
echo ""
echo "  3. Or run Victor AGI LLM with GUI:"
echo "     python VICTOR_AGI_LLM.py"
echo ""
echo "  4. (Optional) Set your OpenAI API key:"
echo "     export OPENAI_API_KEY='your-key-here'"
echo ""
echo "For more information, see README.md and QUICKSTART.md"
echo ""
