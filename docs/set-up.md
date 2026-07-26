# Aegis setup

## Prerequisites

- Python 3.10+
- SigNoz Cloud account (API key + ingestion key)

## Install

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

## Configure `.env`

```env
APP_NAME=aegis
PRODUCT_TITLE=Aegis
OTEL_SERVICE_NAME=aegis

SIGNOZ_URL=https://improved-moose.us2.signoz.cloud
SIGNOZ_API_KEY=...
SIGNOZ_MCP_URL=https://mcp.us2.signoz.cloud/mcp

OTEL_EXPORTER_OTLP_ENDPOINT=https://ingest.us2.signoz.cloud:443
OTEL_EXPORTER_OTLP_HEADERS=signoz-ingestion-key=...
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
```

## Run

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Check:

- http://127.0.0.1:8000/
- http://127.0.0.1:8000/api/v1/health/deep
- http://127.0.0.1:8000/mcp

## SigNoz UI

Filter service **`aegis`** in Services / Traces / Logs.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| MCP ok, query 401 | Use MCP-first path (default) |
| No traces | Ingestion key + wait + service `aegis` |
| Offline RCA | Expected without reasoner keys |
