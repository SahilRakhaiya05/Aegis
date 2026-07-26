# Aegis demo traffic generator (Windows PowerShell)
param(
  [string]$BaseUrl = "http://127.0.0.1:8000",
  [string]$Service = "aegis",
  [int]$WaitSeconds = 15
)

$ErrorActionPreference = "Continue"
Write-Host "======================================"
Write-Host " Aegis · demo traffic generator"
Write-Host " Target: $BaseUrl"
Write-Host " Service: $Service"
Write-Host "======================================"

function Hit([string]$Method, [string]$Path, $Body = $null) {
  try {
    if ($Body -ne $null) {
      Invoke-RestMethod -Method $Method -Uri "$BaseUrl$Path" -ContentType "application/json" -Body ($Body | ConvertTo-Json -Compress) | Out-Null
    } else {
      Invoke-WebRequest -Method $Method -Uri "$BaseUrl$Path" -UseBasicParsing | Out-Null
    }
  } catch {
    # expected for 500/503 chaos endpoints
  }
}

Write-Host "`n[1/6] Warm-up"
1..8 | ForEach-Object { Hit GET "/"; Hit GET "/api/v1/health"; Start-Sleep -Milliseconds 80 }
Write-Host "  ok"

Write-Host "`n[2/6] Healthy orders"
1..12 | ForEach-Object {
  Hit POST "/api/v1/workload/orders" @{ item = "widget"; quantity = 2 }
  Start-Sleep -Milliseconds 80
}
Write-Host "  ok"

Write-Host "`n[3/6] Risky orders (inventory fault)"
1..10 | ForEach-Object {
  Hit POST "/api/v1/workload/orders" @{ item = "bulk-kit"; quantity = 150 }
  Start-Sleep -Milliseconds 120
}
Write-Host "  ok"

Write-Host "`n[4/6] Fault injectors — error / flaky"
1..8 | ForEach-Object {
  Hit GET "/api/v1/chaos/error"
  Hit GET "/api/v1/chaos/flaky"
  Start-Sleep -Milliseconds 120
}
Write-Host "  ok"

Write-Host "`n[5/6] Latency + storm"
Hit GET "/api/v1/chaos/latency"
try {
  Invoke-RestMethod -Method POST -Uri "$BaseUrl/api/v1/chaos/storm?count=8" | Out-Null
} catch {}
Write-Host "  ok"

Write-Host "`n[6/6] Wait ${WaitSeconds}s for SigNoz Cloud ingest…"
Start-Sleep -Seconds $WaitSeconds

Write-Host "`nRunning probe…"
$report = Invoke-RestMethod -Method POST -Uri "$BaseUrl/api/v1/investigate" `
  -ContentType "application/json" `
  -Body (@{
    service = $Service
    lookback_minutes = 30
    include_alerts = $true
  } | ConvertTo-Json)

$report | ConvertTo-Json -Depth 8

Write-Host "`n======================================"
Write-Host " Demo traffic complete"
Write-Host "======================================"
Write-Host "UI:     $BaseUrl/"
Write-Host "Health: $BaseUrl/api/v1/health/deep"
Write-Host "SigNoz: filter service = $Service"
Write-Host "MCP:    POST $BaseUrl/mcp"
if ($report.severity) {
  Write-Host ("Severity: {0} ({1})" -f $report.severity.label, $report.severity.score)
}
if ($report.evidence_source) {
  Write-Host "Evidence: $($report.evidence_source)"
}
