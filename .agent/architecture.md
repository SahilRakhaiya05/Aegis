# Aegis architecture

## Packages

```text
app/
  settings.py              # env-driven config
  bootstrap.py / main.py   # FastAPI app factory + entry
  domain/models.py         # pydantic request/response models
  integrations/
    signoz/                # REST query + SigNoz MCP client + deep links
    llm/router.py          # reasoner backends (auto selection)
  mcp/server.py            # Aegis MCP (JSON-RPC over HTTP)
  observability/           # OTEL tracing/metrics/logs export
  services/                # evidence, investigation, chaos, workload, history
  api/routes/              # REST surface
  web/                     # static desk UI
  prompts/rca.py           # investigation prompts
```

## Request flows

### Probe (UI or REST)

```text
POST /api/v1/investigate
  → services.investigation.investigate
    → services.evidence.collect_evidence
         ├─ SignozMCPClient (preferred)
         └─ SignozQueryClient (fallback)
    → integrations.llm.complete
    → history.push
  → InvestigationReport JSON
```

### Aegis MCP

```text
POST /mcp  { method: tools/call, name: aegis_investigate }
  → app.mcp.server.handle_mcp_request
  → same investigation service path
```

### Telemetry

```text
HTTP middleware + meters
  → OTLP HTTP/protobuf + signoz-ingestion-key
  → SigNoz Cloud ingest (service.name = aegis)
```

## Key env

- `SIGNOZ_URL`, `SIGNOZ_API_KEY`, `SIGNOZ_MCP_URL`
- `OTEL_SERVICE_NAME=aegis`
- `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_EXPORTER_OTLP_HEADERS`
- `LLM_BACKEND`, optional reasoner keys
