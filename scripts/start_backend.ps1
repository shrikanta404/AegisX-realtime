$ErrorActionPreference = 'Stop'
Set-Location "$PSScriptRoot\..\backend"

if (-not (Test-Path '.\venv\Scripts\python.exe')) {
    throw 'Backend virtual environment not found. Run scripts/setup_backend.ps1 first.'
}

& .\venv\Scripts\uvicorn.exe app.main:app --reload
