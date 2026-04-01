@echo off
set "PROJECT_DIR=%~dp0"
set "VENV_PYTHON=%PROJECT_DIR%venv\Scripts\python.exe"

echo [KIRO AI] Starting application...
"%VENV_PYTHON%" "%PROJECT_DIR%uiux\main.py"

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to start uiux\main.py. Trying monitor.py...
    "%VENV_PYTHON%" "%PROJECT_DIR%monitor.py"
)

pause
