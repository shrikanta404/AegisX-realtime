$ErrorActionPreference = 'Stop'

Set-Location "$PSScriptRoot\..\backend"

if (-not (Test-Path '.\venv\Scripts\python.exe')) {
    py -3.13 -m venv venv
}

& .\venv\Scripts\python.exe -m pip install --upgrade pip
& .\venv\Scripts\python.exe -m pip install -r requirements.txt

if (-not (Test-Path '.\.env')) {
    Copy-Item '.\.env.example' '.\.env'
    Write-Host 'Created backend/.env from .env.example. Edit it before starting the API.'
}

Write-Host ''
Write-Host 'Backend dependencies installed.'
Write-Host 'Next steps:'
Write-Host '  1. Edit backend/.env and set DATABASE_URL / optional API keys.'
Write-Host '  2. Make sure PostgreSQL database aegisx_dev exists.'
Write-Host '  3. Run: .\venv\Scripts\python.exe -m alembic upgrade head'
Write-Host '  4. Run: .\venv\Scripts\python.exe -m uvicorn app.main:app --reload'
