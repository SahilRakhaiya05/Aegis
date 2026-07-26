# Aegis demos

Scripts that generate traffic, inject faults, wait for SigNoz Cloud ingestion, and run a probe.

## Prerequisites

```powershell
# server running
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

`.env` must have SigNoz Cloud URL, API key, and OTLP ingestion headers.

## Windows

```powershell
.\demo\generate_incident.ps1
# optional:
.\demo\generate_incident.ps1 -BaseUrl http://127.0.0.1:8000 -Service aegis -WaitSeconds 20
```

## Bash / Git Bash / WSL

```bash
chmod +x demo/generate_incident.sh
./demo/generate_incident.sh
# or
BASE_URL=http://127.0.0.1:8000 SERVICE=aegis ./demo/generate_incident.sh
```

## One-click API demo

```powershell
Invoke-RestMethod -Method POST "http://127.0.0.1:8000/api/v1/demo/run?wait_seconds=12&storm_count=6"
```

## What to show

1. Desk UI status cards (SigNoz API + SigNoz MCP + Aegis MCP)
2. Report: severity, timeline, playbook, export
3. SigNoz Cloud → service **`aegis`**
4. MCP tab → Ping investigate
