@echo off
echo ==============================================
echo Victor Prime - Control Panel Launcher (Windows)
echo ==============================================

echo [1/3] Setting up Python environment...
if not exist "venv" (
    python -m venv venv
)
call venv\Scripts\activate.bat

echo [2/3] Installing/Checking dependencies...
pip install -r requirements.txt

echo [3/3] Launching Victor GUI...
start http://127.0.0.1:7860
python app.py

pause
