# ============================================================
#  Kiro AI - Virtual Environment Runner (PowerShell)
#  Usage: .\run.ps1 <script.py> [arguments...]
#  Example: .\run.ps1 vector.py
#           .\run.ps1 uiux\main.py
#           .\run.ps1 monitor.py
# ============================================================

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $ProjectDir "venv\Scripts\python.exe"

# Check if venv exists
if (-not (Test-Path $VenvPython)) {
    Write-Host "[ERROR] Virtual environment not found at: $ProjectDir\venv" -ForegroundColor Red
    Write-Host "[INFO]  Create it with: python -m venv venv" -ForegroundColor Yellow
    Write-Host "[INFO]  Then install: venv\Scripts\pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

# Check if a script was provided
if ($args.Count -eq 0) {
    Write-Host ""
    Write-Host "  Kiro AI - Virtual Environment Runner" -ForegroundColor Cyan
    Write-Host "  =====================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Usage: .\run.ps1 <script.py> [arguments...]"
    Write-Host ""
    Write-Host "  Available scripts:" -ForegroundColor Green
    Write-Host "    .\run.ps1 vector.py          - Run vector processing"
    Write-Host "    .\run.ps1 monitor.py          - Run file monitor"
    Write-Host "    .\run.ps1 uiux\main.py       - Run the UI application"
    Write-Host "    .\run.ps1 show_vector.py     - Show vector database"
    Write-Host "    .\run.ps1 pdf_reader.py      - Run PDF reader"
    Write-Host ""
    Write-Host "  Python: $VenvPython" -ForegroundColor DarkGray
    Write-Host ""
    exit 0
}

# Run the script with venv Python
Write-Host "[Kiro] Using venv Python: $VenvPython" -ForegroundColor Green
Write-Host "[Kiro] Running: $args" -ForegroundColor Green
Write-Host "----------------------------------------" -ForegroundColor DarkGray

& $VenvPython @args
