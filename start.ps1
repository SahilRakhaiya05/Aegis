#Requires -Version 5.1
<#
.SYNOPSIS
  One-command launcher for Aegis (venv, deps, .env, free port, uvicorn).

.EXAMPLE
  .\start.ps1
  .\start.ps1 -Port 8000 -NoReload
  .\start.ps1 -SkipPortKill
#>
[CmdletBinding()]
param(
  [int]$Port = 8000,
  [string]$HostAddress = "127.0.0.1",
  [switch]$NoReload,
  [switch]$SkipPortKill,
  [switch]$Reinstall
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Show-AegisBanner {
  Write-Host ""
  Write-Host "  ========================================" -ForegroundColor Cyan
  Write-Host "               A E G I S" -ForegroundColor Cyan
  Write-Host "      SRE copilot for SigNoz" -ForegroundColor Cyan
  Write-Host "  ========================================" -ForegroundColor Cyan
  Write-Host ""
}

function Find-PythonLauncher {
  $candidates = @(
    @{ Cmd = "py"; Args = @("-3.13") },
    @{ Cmd = "py"; Args = @("-3.12") },
    @{ Cmd = "py"; Args = @("-3.11") },
    @{ Cmd = "py"; Args = @("-3") },
    @{ Cmd = "python"; Args = @() },
    @{ Cmd = "python3"; Args = @() }
  )
  $pyCode = 'import sys; print("%d.%d" % (sys.version_info[0], sys.version_info[1]))'
  foreach ($c in $candidates) {
    if (-not (Get-Command $c.Cmd -ErrorAction SilentlyContinue)) { continue }
    try {
      $ver = & $c.Cmd @($c.Args + @("-c", $pyCode)) 2>$null
      if ($LASTEXITCODE -ne 0 -or -not $ver) { continue }
      $ver = ([string]$ver).Trim()
      $parts = $ver.Split(".")
      if ($parts.Count -lt 2) { continue }
      $major = [int]$parts[0]
      $minor = [int]$parts[1]
      if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) { continue }
      return @{
        Launcher = $c.Cmd
        Args     = $c.Args
        Version  = $ver
      }
    } catch {
      continue
    }
  }
  throw "Python 3.10+ not found. Install Python 3.11+ (or the Windows py launcher) and retry."
}

function Initialize-AegisVenv {
  param([hashtable]$Python, [switch]$Force)
  $venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
  $uvicornExe = Join-Path $PSScriptRoot ".venv\Scripts\uvicorn.exe"

  if ($Force -and (Test-Path ".\.venv")) {
    Write-Host "Removing existing .venv (Reinstall)..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force .\.venv
  }

  if (-not (Test-Path $venvPython)) {
    Write-Host "Creating virtualenv with Python $($Python.Version)..." -ForegroundColor Yellow
    & $Python.Launcher @($Python.Args + @("-m", "venv", ".venv"))
    if (-not (Test-Path $venvPython)) {
      throw "Failed to create .venv"
    }
  }

  if ((-not (Test-Path $uvicornExe)) -or $Force) {
    Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor Yellow
    & $venvPython -m pip install -U pip --quiet
    & $venvPython -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
      throw "pip install failed"
    }
  }

  if (-not (Test-Path $uvicornExe)) {
    throw "uvicorn not found after install. Check requirements.txt"
  }
}

function Initialize-AegisEnvFile {
  if (Test-Path ".\.env") { return }
  if (-not (Test-Path ".\.env.example")) {
    Write-Host "Warning: .env.example missing - create .env manually." -ForegroundColor Yellow
    return
  }
  Copy-Item .\.env.example .\.env
  Write-Host "Created .env from .env.example" -ForegroundColor Yellow
  Write-Host "  -> set SIGNOZ_URL, SIGNOZ_API_KEY, and OTEL_EXPORTER_OTLP_HEADERS" -ForegroundColor Yellow
}

function Clear-AegisPort {
  param([int]$ListenPort)
  try {
    $pids = Get-NetTCPConnection -LocalPort $ListenPort -State Listen -ErrorAction SilentlyContinue |
      Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($procId in $pids) {
      if (-not $procId -or $procId -eq 0) { continue }
      $name = (Get-Process -Id $procId -ErrorAction SilentlyContinue).ProcessName
      Write-Host "Freeing port $ListenPort (PID $procId / $name)..." -ForegroundColor Yellow
      Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    }
  } catch {
    # Get-NetTCPConnection may fail on some hosts - ignore
  }
}

# --- main ---
Show-AegisBanner

$py = Find-PythonLauncher
Write-Host "Python: $($py.Version) via $($py.Launcher)" -ForegroundColor DarkGray

Initialize-AegisVenv -Python $py -Force:$Reinstall
Initialize-AegisEnvFile

if (-not $SkipPortKill) {
  Clear-AegisPort -ListenPort $Port
}

$reloadArgs = @()
if (-not $NoReload) {
  $reloadArgs = @("--reload")
}

Write-Host ""
Write-Host "Starting Aegis..." -ForegroundColor Green
Write-Host "  UI      http://${HostAddress}:${Port}/"
Write-Host "  Docs    http://${HostAddress}:${Port}/docs"
Write-Host "  Health  http://${HostAddress}:${Port}/api/v1/health"
Write-Host "  Deep    http://${HostAddress}:${Port}/api/v1/health/deep"
Write-Host "  MCP     http://${HostAddress}:${Port}/mcp"
Write-Host "  Stop    Ctrl+C"
Write-Host ""

$uvicornExe = Join-Path $PSScriptRoot ".venv\Scripts\uvicorn.exe"
& $uvicornExe "app.main:app" --host $HostAddress --port $Port @reloadArgs
exit $LASTEXITCODE
