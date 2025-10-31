@echo off
REM #############################################################
REM Victor Prime AGI - One-Click Setup Script (Windows)
REM #############################################################

echo ==========================================
echo   Victor Prime AGI - Setup
echo ==========================================
echo.

REM Check Python installation
echo Checking Python installation...
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.8 or newer from https://www.python.org/
    pause
    exit /b 1
)

REM Check Python version
python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python 3.8 or newer is required.
    python --version
    pause
    exit /b 1
)

for /f "delims=" %%i in ('python -c "import sys; print('.'.join(map(str, sys.version_info[:2])))"') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% detected
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created
) else (
    echo [WARN] Virtual environment already exists
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip --quiet
echo [OK] pip upgraded
echo.

REM Install dependencies
echo Installing dependencies...
echo This may take a few minutes...
pip install -r requirements.txt --quiet
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

REM Install package in development mode
echo Installing Victor Prime AGI in development mode...
pip install -e . --quiet
echo [OK] Victor Prime AGI installed
echo.

REM Create necessary directories
echo Creating necessary directories...
if not exist "victor_plugins" mkdir victor_plugins
if not exist "victor_bando_persistent" mkdir victor_bando_persistent
if not exist "logs" mkdir logs
echo [OK] Directories created
echo.

echo ==========================================
echo   Setup Complete!
echo ==========================================
echo.
echo To get started:
echo   1. Activate the virtual environment:
echo      venv\Scripts\activate.bat
echo.
echo   2. Run Victor Prime Core:
echo      python -m victor_core.main
echo.
echo   3. Or run Victor AGI LLM with GUI:
echo      python VICTOR_AGI_LLM.py
echo.
echo   4. (Optional) Set your OpenAI API key:
echo      set OPENAI_API_KEY=your-key-here
echo.
echo For more information, see README.md and QUICKSTART.md
echo.
pause
