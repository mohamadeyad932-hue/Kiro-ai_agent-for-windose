@echo off
title KIRO AI AGENT - SMART CLEANER
color 0B

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
    exit
)

:: Run the Main Launcher
python run_project.py

if %errorlevel% neq 0 (
    echo.
    echo [!] There was a system error during execution.
    pause
)
