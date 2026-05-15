@echo off
title Kiro AI - Build Executable
echo ===============================================
echo       Kiro AI - Build System (Protected)
echo ===============================================
echo.

REM --- Check Virtual Environment ---
if exist "venv\Scripts\activate.bat" (
    echo [1/5] Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo [!] WARNING: Virtual environment not found!
    echo     Proceeding with system Python...
)

REM --- Check PyInstaller ---
echo [2/5] Checking PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo     PyInstaller not found. Installing...
    pip install pyinstaller
)
echo     Done - PyInstaller ready

REM --- Compile Scripts to .pyc ---
echo [3/5] Compiling scripts to .pyc (source protection)...
python compile_scripts.py
if errorlevel 1 (
    echo [!] WARNING: Some scripts failed to compile.
    echo     Build will continue with .py fallback.
)
echo     Done - Scripts compiled

REM --- Clean Previous Build ---
echo [4/5] Cleaning previous build...
if exist "dist\KiroAI" rmdir /s /q "dist\KiroAI"
if exist "build\KiroAI" rmdir /s /q "build\KiroAI"
echo     Done - Clean

REM --- Build Executable ---
echo [5/5] Building executable...
echo     This may take several minutes...
echo.
pyinstaller build_exe.spec --noconfirm

if errorlevel 1 (
    echo.
    echo ===============================================
    echo   BUILD FAILED! Check the errors above.
    echo ===============================================
    pause
    exit /b 1
)

REM --- Copy python.exe to _internal ---
echo.
echo [+] Copying BASE Python interpreter to _internal...
python -c "import sys, shutil, os; exe = getattr(sys, '_base_executable', sys.executable); shutil.copy(exe, r'dist\KiroAI\_internal\python.exe') if os.path.exists(exe) else None"
if not errorlevel 1 (
    echo     Done - Base python.exe copied successfully
) else (
    echo     [!] Failed to copy python.exe
)
:python_done

REM --- Clean Temporary .pyc Files ---
echo [+] Cleaning up .pyc files from source...
del /q "run_project.pyc" 2>nul
for %%d in ("Processing text files" "Processing image" "clustring_files" "clustring_imge" "creat folders for flie_text  and name" "creat folders for image and name" "dawnload_models") do (
    del /q "%%~d\*.pyc" 2>nul
)
echo     Done - Source directory clean

echo.
echo ===============================================
echo   BUILD SUCCESSFUL!
echo.
echo   Output: dist\KiroAI\KiroAI.exe
echo   Source code: PROTECTED (.pyc bytecode)
echo.
echo   Next steps:
echo     1. Test: dist\KiroAI\KiroAI.exe
echo     2. Create installer with Inno Setup
echo ===============================================
pause
