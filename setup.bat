@echo off
REM Victor LLM One-Click Setup Script for Windows
REM This script creates necessary directories, installs dependencies, and creates a desktop shortcut

echo =====================================
echo Victor LLM One-Click Setup
echo =====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.8 or newer from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo [1/5] Python found:
python --version
echo.

REM Create necessary directories
echo [2/5] Creating necessary directories...
if not exist "victor_plugins" mkdir victor_plugins
if not exist "bando_persistent" mkdir bando_persistent
if not exist "models" mkdir models
echo Directories created successfully.
echo.

REM Install dependencies
echo [3/5] Installing Python dependencies...
echo This may take a few minutes...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)
echo Dependencies installed successfully.
echo.

REM Create desktop shortcut
echo [4/5] Creating desktop shortcut...
set SCRIPT_DIR=%~dp0
set SHORTCUT_PATH=%USERPROFILE%\Desktop\Victor LLM.lnk
set TARGET_PATH=%SCRIPT_DIR%run_victor.bat
REM Icon index 13 in SHELL32.dll is typically a star/application icon (may vary by Windows version)
set ICON_PATH=%SystemRoot%\System32\SHELL32.dll,13

REM Create VBS script to create shortcut
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%SHORTCUT_PATH%" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%TARGET_PATH%" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%SCRIPT_DIR%" >> CreateShortcut.vbs
echo oLink.IconLocation = "%ICON_PATH%" >> CreateShortcut.vbs
echo oLink.Description = "Run Victor LLM AI System" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs

cscript //nologo CreateShortcut.vbs
del CreateShortcut.vbs

if exist "%SHORTCUT_PATH%" (
    echo Desktop shortcut created successfully!
) else (
    echo WARNING: Failed to create desktop shortcut.
    echo You can manually run the application using run_victor.bat
)
echo.

REM Verify run script exists
if not exist "run_victor.bat" (
    echo [5/5] WARNING: run_victor.bat not found!
    echo Please ensure run_victor.bat is present in the repository.
) else (
    echo [5/5] Run script found: run_victor.bat
)
echo.

echo =====================================
echo Setup completed successfully!
echo =====================================
echo.
echo You can now:
echo 1. Double-click "Victor LLM" shortcut on your desktop
echo 2. Run run_victor.bat from this directory
echo 3. Run: python -m victor_core.main
echo.
echo Note: Make sure to set your OPENAI_API_KEY environment variable
echo if you plan to use OpenAI features.
echo.
pause
