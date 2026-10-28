$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot

Set-Location "$root\backend"
if (-not (Test-Path '.\venv\Scripts\python.exe')) {
    throw 'Backend virtual environment not found. Run scripts/setup_backend.ps1 first.'
}

& .\venv\Scripts\python.exe -m compileall -q app migrations tests
$env:PYTHONPATH = '.'
& .\venv\Scripts\python.exe .\tests\test_offline.py

Set-Location "$root\frontend"
if (-not (Test-Path '.\node_modules')) {
    throw 'Frontend dependencies not found. Run npm install first.'
}

& node .\node_modules\typescript\bin\tsc -b
Write-Host 'AegisX verification checks passed.'
