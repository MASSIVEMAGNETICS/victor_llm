# Victor Prime AGI - Quick Start Guide

Welcome to Victor Prime AGI! This guide will help you get up and running in minutes.

## 🚀 One-Click Setup

### For Linux/Mac:
```bash
chmod +x setup.sh
./setup.sh
```

### For Windows:
```cmd
setup.bat
```

The setup script will:
- Check your Python installation (requires Python 3.8+)
- Create a virtual environment
- Install all dependencies
- Set up the project structure

## 📋 Prerequisites

- **Python 3.8 or newer** - [Download Python](https://www.python.org/downloads/)
- **OpenAI API Key** (optional, for LLM features) - [Get API Key](https://platform.openai.com/api-keys)

## 🎯 Running Victor Prime

### Option 1: Victor Core (Advanced Framework)

The core AGI framework with modular sectors and advanced features:

```bash
# Activate virtual environment first
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate.bat  # Windows

# Run the core
python -m victor_core.main
```

**What it does:**
- Initializes the VictorBrain with all cognitive sectors
- Sets up memory systems and NLP processing
- Runs the main AGI processing loop
- Demonstrates the modular architecture

### Option 2: Victor AGI LLM (GUI Interface)

A graphical interface for interacting with the AGI:

```bash
python VICTOR_AGI_LLM.py
```

**Features:**
- Interactive GUI for chat and commands
- Module management interface
- Timeline and state management
- Visual feedback and controls

### Option 3: Dataset Trainer GUI

For training and fine-tuning models:

```bash
python bando_dataset_trainer_gui_v1.0.0-BANDO-GODCORE.py
```

## 🔧 Configuration

### Setting OpenAI API Key

For features that use OpenAI's language models:

**Linux/Mac:**
```bash
export OPENAI_API_KEY='your-api-key-here'
```

**Windows:**
```cmd
set OPENAI_API_KEY=your-api-key-here
```

### Adjusting Log Levels

Control verbosity of logging output:

```bash
export VICTOR_LOG_LEVEL=DEBUG  # Options: DEBUG, INFO, WARN, ERROR, CRITICAL
```

## 📁 Project Structure

```
victor_llm/
├── victor_core/          # Core AGI framework
│   ├── brain.py          # Main VictorBrain orchestrator
│   ├── sectors/          # Cognitive sectors (Input, Memory, etc.)
│   ├── memory/           # Memory systems
│   ├── nlp/              # Natural language processing
│   └── main.py           # Entry point
├── victor_modules/       # Extended modules
│   ├── quantum/          # Quantum processing simulation
│   └── fractal_agi/      # Fractal persistence
├── victor_plugins/       # Plugin directory
├── VICTOR_AGI_LLM.py    # GUI interface
├── setup.sh/setup.bat   # Setup scripts
└── requirements.txt     # Dependencies
```

## 🎨 GUI Features

### Victor AGI Command Center

The GUI provides:

1. **Chat Interface**: Interact with the AGI through natural language
2. **Module Manager**: View and manage loaded modules
3. **Variable Inspector**: Inspect system variables
4. **Timeline Management**: Save states and undo/redo operations
5. **Code Execution**: Run Python code in the AGI context
6. **Diagnostics**: System health and performance monitoring

### Navigation Tips

- Use the chat input at the bottom for conversational interaction
- Access module management through the "Modules" tab
- View system state through the "Variables" panel
- Use timeline controls for state management

## 🐛 Troubleshooting

### Common Issues

**Issue**: "ModuleNotFoundError" when running scripts
**Solution**: Make sure you've activated the virtual environment first

**Issue**: Import errors for tkinter
**Solution**: Install tkinter:
- Ubuntu/Debian: `sudo apt-get install python3-tk`
- Mac: Included with Python from python.org
- Windows: Included with Python installer

**Issue**: FAISS-related errors
**Solution**: Make sure numpy is compatible. Try: `pip install --upgrade numpy faiss-cpu`

**Issue**: "No plugins found" warning
**Solution**: This is normal on first run. The system creates a dummy plugin automatically.

### Getting Help

1. Check the main [README.md](README.md) for detailed documentation
2. Review error messages in the console output
3. Check the generated log files in `logs/` directory
4. Set `VICTOR_LOG_LEVEL=DEBUG` for more detailed information

## 🔐 Security Notes

- **Never commit API keys** to version control
- Use environment variables for sensitive configuration
- Review plugin code before loading into the system
- The PrimeLoyaltySector enforces ethical guidelines

## 📚 Next Steps

1. **Explore the Core**: Run `python -m victor_core.main` to see the modular system in action
2. **Try the GUI**: Launch `VICTOR_AGI_LLM.py` for interactive exploration
3. **Read the Architecture**: Review `README.md` for system architecture details
4. **Create Plugins**: Add custom functionality in the `victor_plugins/` directory
5. **Experiment**: Modify sectors and components to customize behavior

## 💡 Tips & Best Practices

- **Start Simple**: Begin with the GUI interface to understand the system
- **Read Logs**: The system provides detailed logging for troubleshooting
- **Use Virtual Env**: Always activate the virtual environment before running
- **Backup State**: The system auto-saves memory state to `victor_bando_persistent/`
- **Explore Code**: The codebase is well-documented with inline comments

## 🎓 Learning Resources

- **Main README**: Detailed architecture and component documentation
- **Code Comments**: Inline documentation in source files
- **Example Plugins**: Reference the dummy plugin structure
- **Sector Code**: Review sector implementations for patterns

---

**Welcome to Victor Prime AGI! Happy exploring! 🚀**
