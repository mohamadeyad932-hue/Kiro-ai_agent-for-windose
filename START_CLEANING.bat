@echo off
chcp 65001 >nul 2>nul
title KIRO AI AGENT - SMART CLEANER
color 0B

:: Navigate to the project directory (where this .bat file is located)
cd /d "%~dp0"

echo ==================================================
echo         KIRO AI AGENT - MASTER LAUNCHER
echo            System Management Core
echo ==================================================
echo.

:: Check for Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [!] ERROR: Python is not installed or not in PATH.
    pause
    exit /b 1
)

:: Check for venv and activate it if it exists
if exist "venv\Scripts\activate.bat" (
    echo [*] Activating virtual environment...
    call venv\Scripts\activate.bat
    echo [✓] Virtual environment activated.
    echo.
)

:: Pass all arguments to run_project.py (supports both interactive and CLI mode)
:: Interactive:  START_CLEANING.bat
:: CLI example:  START_CLEANING.bat --mode text --desktop
python run_project.py %*

if %errorlevel% neq 0 (
    echo.
    echo [!] There was a system error during execution.
)

echo.
pause
