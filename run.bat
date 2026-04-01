@echo off
REM ============================================================
REM  Kiro AI - Virtual Environment Runner
REM  Usage: run.bat <script.py> [arguments...]
REM  Example: run.bat vector.py
REM           run.bat uiux\main.py
REM           run.bat monitor.py
REM ============================================================

REM Get the directory where this batch file lives
set "PROJECT_DIR=%~dp0"

REM Path to the venv Python
set "VENV_PYTHON=%PROJECT_DIR%venv\Scripts\python.exe"

REM Check if venv exists
if not exist "%VENV_PYTHON%" (
    echo [ERROR] Virtual environment not found at: %PROJECT_DIR%venv
    echo [INFO]  Create it with: python -m venv venv
    echo [INFO]  Then install requirements: venv\Scripts\pip install -r requirements.txt
    exit /b 1
)

REM Check if a script was provided
if "%~1"=="" (
    echo.
    echo  Kiro AI - Virtual Environment Runner
    echo  =====================================
    echo.
    echo  Usage: run.bat ^<script.py^> [arguments...]
    echo.
    echo  Available scripts:
    echo    run.bat vector.py          - Run vector processing
    echo    run.bat monitor.py         - Run file monitor
    echo    run.bat uiux\main.py       - Run the UI application
    echo    run.bat show_vector.py     - Show vector database
    echo    run.bat pdf_reader.py      - Run PDF reader
    echo.
    echo  Python: %VENV_PYTHON%
    echo.
    exit /b 0
)

REM Activate the venv and run the script
echo [Kiro] Using venv Python: %VENV_PYTHON%
echo [Kiro] Running: %*
echo ----------------------------------------
"%VENV_PYTHON%" %*
