@echo off
REM Victor LLM Run Script for Windows
REM This script runs the Victor LLM AI System

cd /d "%~dp0"

echo =====================================
echo Victor LLM AI System
echo =====================================
echo.
echo Starting Victor Core...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please run setup.bat first.
    pause
    exit /b 1
)

REM Run Victor Core
python -m victor_core.main

REM Keep the window open if there's an error
if errorlevel 1 (
    echo.
    echo An error occurred. Check the output above.
    pause
)
