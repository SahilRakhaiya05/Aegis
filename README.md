# Aegis

**SRE copilot for SigNoz** — OpenTelemetry in, root-cause analysis out.

Aegis exports telemetry to **SigNoz Cloud**, collects evidence through **SigNoz MCP**, exposes **Aegis MCP** for agents, and returns structured RCA reports in a white desk UI.

```text
Faults / live traffic
        │
        ▼
OpenTelemetry ──OTLP──► SigNoz Cloud
        │                    │
        │            SigNoz MCP (evidence)
        ▼                    │
     Aegis desk ◄────────────┘
        │
   ┌────┴────┐
   ▼         ▼
Aegis MCP  Reasoner
  /mcp    online|offline
   │         │
   └────┬────┘
        ▼
  RCA report · severity · timeline · playbook · export
```

---

## Live stack

| Piece | Value |
|-------|--------|
| Product | **Aegis** |
| OTEL service | `aegis` |
| SigNoz Cloud | https://improved-moose.us2.signoz.cloud |
| SigNoz MCP | https://mcp.us2.signoz.cloud/mcp |
| Aegis MCP | `POST /mcp` |
| OTLP | `https://ingest.us2.signoz.cloud:443` |
| UI | http://127.0.0.1:8000/ |
| Docs | http://127.0.0.1:8000/docs |

Secrets only in `.env` (gitignored).

---

## Features

- White **desk UI** (Home · Probe · Faults · MCP · SigNoz)
- **SigNoz MCP** evidence (traces, logs, alerts)
- **Aegis MCP** agent tools (`aegis_*`)
- Structured RCA: summary, root cause, impact, fix, confidence
- **Severity score**, **timeline**, **playbook**, **export** (MD/JSON/copy)
- Pipeline stepper: Collect → Reason → Report
- Fault injectors + inventory-fault workload
- One-click dry-run + `demo/` traffic scripts
- Session stats + history

---

## Quick start

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# set SIGNOZ_URL, SIGNOZ_API_KEY, OTEL headers
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/

### Docker

```powershell
docker compose up --build
```

---

## Demo (perfect path)

### Option A — UI

1. Open the desk → confirm SigNoz API + both MCPs.  
2. Click **Full dry-run**.  
3. Show severity, timeline, playbook, export.  
4. SigNoz Cloud → service **`aegis`**.  
5. MCP tab → **Ping investigate**.

### Option B — PowerShell script

```powershell
.\demo\generate_incident.ps1
```

### Option C — API

```powershell
Invoke-RestMethod -Method POST "http://127.0.0.1:8000/api/v1/demo/run?wait_seconds=12"
```

### Option D — Bash

```bash
./demo/generate_incident.sh
```

---

## API (v1)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Desk UI |
| GET | `/api/v1/health` | Liveness |
| GET | `/api/v1/health/deep` | SigNoz + dual MCP + OTEL |
| GET | `/api/v1/signoz/links` | Deep links |
| GET | `/api/v1/signoz/mcp/tools` | SigNoz MCP tools |
| GET | `/api/v1/mcp/tools` | Aegis MCP tools |
| GET/POST | `/mcp` | Aegis MCP JSON-RPC |
| POST | `/api/v1/investigate` | Full RCA |
| POST | `/api/v1/investigate/evidence` | Evidence only |
| GET | `/api/v1/investigate/history` | History |
| GET | `/api/v1/investigate/stats` | Session stats |
| GET | `/api/v1/investigate/history/{id}/export.md` | Markdown export |
| POST | `/api/v1/chaos/*` | Fault injectors |
| POST | `/api/v1/demo/run` | End-to-end dry-run |
| POST | `/api/v1/workload/orders` | Demo orders |

Legacy aliases under `/api/v1/incidents/*` and `/api/v1/orders` remain for older scripts.

---

## Layout

```text
.agent/              agent workspace
app/                 FastAPI application
  mcp/               Aegis MCP server
  integrations/      SigNoz + reasoner
  services/          evidence, investigation, chaos, …
  web/               white desk UI
demo/                traffic + probe scripts
docs/                human documentation
tests/               pytest suite
```

---

## Configuration

| Variable | Purpose |
|----------|---------|
| `SIGNOZ_URL` | Cloud instance |
| `SIGNOZ_API_KEY` | Service account key |
| `SIGNOZ_MCP_URL` | Hosted MCP |
| `OTEL_SERVICE_NAME` | `aegis` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Ingest URL |
| `OTEL_EXPORTER_OTLP_HEADERS` | `signoz-ingestion-key=…` |
| `LLM_BACKEND` | `auto` / offline / provider |
| Reasoner keys | Optional (UI shows online/offline only) |

---

## Tests

```powershell
pytest -q
```

---

## More docs

- [System design](SystemDesign.md)
- [Setup](docs/set-up.md)
- [Analyzer](docs/analyzer.md)
- [Demos](demo/README.md)
- [Agent workspace](.agent/README.md)

## Security

Never commit `.env`. Rotate exposed keys.

## License

See `LICENSE`.
