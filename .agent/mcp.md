# MCP catalog

## SigNoz MCP (external)

| Field | Value |
|-------|--------|
| URL | `SIGNOZ_MCP_URL` (e.g. `https://mcp.us2.signoz.cloud/mcp`) |
| Auth | `SIGNOZ-API-KEY` + `X-SigNoz-URL` headers |
| Client | `app/integrations/signoz/mcp.py` |
| Used for | search traces/logs, alerts, trace details, services |

## Aegis MCP (Aegis)

| Field | Value |
|-------|--------|
| URL | `POST /mcp` on this app |
| Discovery | `GET /mcp`, `GET /api/v1/mcp/tools` |
| Server | `app/mcp/server.py` |
| Name | `AegisMCP` |

### Tools

| Name | Description |
|------|-------------|
| `aegis_health` | Dual MCP + API health snapshot |
| `aegis_investigate` | Full RCA for a service/window |
| `aegis_evidence` | Evidence bundle only |
| `aegis_history` | Recent in-memory reports |
| `aegis_fault` | Inject error/latency/flaky/storm |
| `aegis_signoz_links` | Deep links into SigNoz UI |

### Minimal initialize

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": { "name": "agent", "version": "1" }
  }
}
```

### Call investigate

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "aegis_investigate",
    "arguments": {
      "service": "aegis",
      "lookback_minutes": 30,
      "include_alerts": true
    }
  }
}
```
