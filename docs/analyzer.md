# Aegis analyzer

## Pipeline

```text
Faults / traffic
  → OTEL → SigNoz Cloud
  → collect evidence (SigNoz MCP → REST fallback)
  → reasoner (online | offline)
  → enrichment (severity, timeline, playbook, links)
  → report + history + export
```

## Code map

| Module | Role |
|--------|------|
| `app/services/evidence.py` | Collect traces/logs/alerts |
| `app/integrations/signoz/mcp.py` | SigNoz MCP client |
| `app/integrations/signoz/query_api.py` | Query Range REST |
| `app/integrations/llm/router.py` | Reasoner backends |
| `app/services/enrichment.py` | Severity / timeline / playbook |
| `app/services/investigation.py` | Orchestration |
| `app/mcp/server.py` | Aegis MCP tools |

## API

```bash
# Full RCA
curl -s -X POST http://127.0.0.1:8000/api/v1/investigate \
  -H "Content-Type: application/json" \
  -d '{"service":"aegis","lookback_minutes":30}'

# Evidence only
curl -s -X POST http://127.0.0.1:8000/api/v1/investigate/evidence \
  -H "Content-Type: application/json" \
  -d '{"service":"aegis","lookback_minutes":30}'

# Export markdown
curl -s http://127.0.0.1:8000/api/v1/investigate/history/<id>/export.md
```

## Aegis MCP

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "aegis_investigate",
    "arguments": { "service": "aegis", "lookback_minutes": 30 }
  }
}
```

POST to `/mcp`.

## Notes

- Prefer SigNoz MCP; REST is fallback when traces/logs are empty.  
- Some Cloud keys authorize MCP but not `/api/v5/query_range` (401) — expected.  
- Service name in SigNoz: **`aegis`**.
