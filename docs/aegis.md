# Aegis product guide

## Mission

Reduce time-to-understanding during incidents by automating evidence collection from SigNoz and producing a structured RCA.

## Surfaces

| Surface | Path |
|---------|------|
| Desk UI | `/` |
| REST API | `/api/v1/*` |
| Aegis MCP | `/mcp` |
| SigNoz Cloud | configured instance URL |

## Flows

1. **Fault → telemetry** — injectors hit the API; OTEL exports to SigNoz as `aegis`.
2. **Probe** — MCP evidence → reasoner → report.
3. **Agent** — external tools call `aegis_investigate` via Aegis MCP.

## Reasoner

The UI never brands models. Configure keys in `.env` for online reasoning; otherwise offline reports still return usable structure for demos.
