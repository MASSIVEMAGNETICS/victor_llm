# Victor LLM Quick Start Guide

This guide will help you get Victor LLM up and running quickly with our one-click setup.

## Prerequisites

- **Python 3.8 or newer** installed on your system
  - Windows: Download from [python.org](https://www.python.org/downloads/)
  - Linux: Usually pre-installed, or install via package manager
  - macOS: Install via Homebrew: `brew install python3`

- **Git** (to clone the repository)
- **Internet connection** (for installing dependencies)

## Installation

### Windows

1. **Install Python** (if not already installed)
   - Download Python 3.8+ from [python.org](https://www.python.org/downloads/)
   - ⚠️ **Important**: Check "Add Python to PATH" during installation

2. **Clone the Repository**
   ```cmd
   git clone https://github.com/MASSIVEMAGNETICS/victor_llm.git
   cd victor_llm
   ```

3. **Run the Setup Script**
   - Double-click `setup.bat` in the repository folder
   - OR open Command Prompt in the folder and run:
     ```cmd
     setup.bat
     ```

4. **Wait for Installation**
   - The script will install all dependencies (may take 5-10 minutes)
   - A desktop shortcut will be created automatically

5. **Run Victor LLM**
   - Double-click the "Victor LLM" shortcut on your desktop
   - OR double-click `run_victor.bat` in the repository folder

### Linux / macOS

1. **Install Python** (if not already installed)
   - Linux: `sudo apt-get install python3 python3-pip` (Ubuntu/Debian)
   - macOS: `brew install python3`

2. **Clone the Repository**
   ```bash
   git clone https://github.com/MASSIVEMAGNETICS/victor_llm.git
   cd victor_llm
   ```

3. **Run the Setup Script**
   ```bash
   bash setup.sh
   ```

4. **Wait for Installation**
   - The script will install all dependencies (may take 5-10 minutes)
   - A desktop shortcut will be created automatically

5. **Run Victor LLM**
   - Double-click `victor_llm.desktop` on your desktop
   - OR run in terminal:
     ```bash
     ./run_victor.sh
     ```

## Configuration

### OpenAI API Key (Optional)

If you want to use OpenAI features, set your API key as an environment variable:

**Windows:**
```cmd
setx OPENAI_API_KEY "your-api-key-here"
```

**Linux/macOS:**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

To make it permanent on Linux/macOS, add the line to your `~/.bashrc` or `~/.zshrc`:
```bash
echo 'export OPENAI_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

## Troubleshooting

### "Python is not recognized" (Windows)
- Python is not in your PATH
- Reinstall Python and check "Add Python to PATH"
- OR manually add Python to PATH in System Environment Variables

### "command not found: python3" (Linux/macOS)
- Python 3 is not installed
- Install it using your package manager:
  - Ubuntu/Debian: `sudo apt-get install python3`
  - macOS: `brew install python3`

### Permission Denied (Linux/macOS)
- Make scripts executable:
  ```bash
  chmod +x setup.sh run_victor.sh
  ```

### Dependency Installation Fails
- Check your internet connection
- Try updating pip first:
  ```bash
  python3 -m pip install --upgrade pip
  ```
- Install dependencies manually:
  ```bash
  pip install -r requirements.txt
  ```

### Desktop Shortcut Doesn't Work
- Run the application directly using the run scripts:
  - Windows: `run_victor.bat`
  - Linux/macOS: `./run_victor.sh`

## What Gets Installed?

The setup script will:
1. ✅ Create necessary directories (`victor_plugins`, `bando_persistent`, `models`)
2. ✅ Install Python dependencies from `requirements.txt`:
   - openai, numpy, scipy, torch, tqdm
   - pyttsx3, pydub, opencv-python
   - faiss-cpu (for vector search)
3. ✅ Create a desktop shortcut for easy access
4. ✅ Create run scripts for quick launching

## Next Steps

After installation, you can:

1. **Train a Model**: See `TRAINING_GUIDE.md` for model training instructions
2. **Add Plugins**: Create plugins in the `victor_plugins` directory
3. **Configure**: Adjust settings in `victor_core/config.py`
4. **Explore**: Check out the documentation in the `docs` folder

## Getting Help

- Read the main `README.md` for detailed documentation
- Check `IMPLEMENTATION_SUMMARY.md` for architecture details
- Visit the GitHub repository for issues and discussions

## Manual Installation (Advanced)

If you prefer to install manually without the scripts:

```bash
# Create directories
mkdir -p victor_plugins bando_persistent models

# Install dependencies
pip install -r requirements.txt

# Run Victor
python -m victor_core.main
```

---

**Enjoy using Victor LLM! 🚀**
