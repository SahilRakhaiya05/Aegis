# Start Aegis desk API + UI on http://127.0.0.1:8000
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path .\.venv\Scripts\uvicorn.exe)) {
  Write-Host "Creating venv and installing dependencies..."
  py -3.13 -m venv .venv
  .\.venv\Scripts\python.exe -m pip install -U pip
  .\.venv\Scripts\pip.exe install -r requirements.txt
  .\.venv\Scripts\pip.exe install "setuptools==70.0.0"
}

if (-not (Test-Path .\.env)) {
  Copy-Item .env.example .env
  Write-Host "Created .env from .env.example — add your SigNoz keys."
}

# Free port 8000 if something else holds it
try {
  $pids = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique
  foreach ($procId in $pids) {
    Write-Host "Stopping process on port 8000: $procId"
    Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
  }
} catch {}

Write-Host ""
Write-Host "Aegis starting..."
Write-Host "  UI:    http://127.0.0.1:8000/"
Write-Host "  Docs:  http://127.0.0.1:8000/docs"
Write-Host "  Health:http://127.0.0.1:8000/api/v1/health"
Write-Host "  MCP:   http://127.0.0.1:8000/mcp"
Write-Host ""

& .\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload
