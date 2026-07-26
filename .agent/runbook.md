# Aegis runbook

## Start

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Verify

```powershell
curl http://127.0.0.1:8000/api/v1/health
curl http://127.0.0.1:8000/api/v1/health/deep
curl http://127.0.0.1:8000/api/v1/mcp/tools
```

## Demo

```powershell
.\demo\generate_incident.ps1
# or
Invoke-RestMethod -Method POST "http://127.0.0.1:8000/api/v1/demo/run?wait_seconds=12"
```

UI: http://127.0.0.1:8000/  
SigNoz service filter: **aegis**  
Aegis MCP: `POST /mcp`

## Tests

```powershell
pytest -q
```
