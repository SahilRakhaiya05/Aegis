# Coding conventions (Aegis)

## Naming

- Product: **Aegis**
- Python package root: `app` (not renamed to `aegis` to avoid churn)
- Service / OTEL: `aegis`
- Aegis MCP tools: `aegis_*`
- Metrics: `aegis.*`

## UI

- Light/white desk by default
- No vendor model brand names in copy
- Reasoner status: `online` | `offline` only
- Keep SigNoz + Aegis MCP visible as first-class

## Backend

- Prefer `services/` for business logic; routes stay thin
- MCP tools should call the same services as REST
- Evidence collection: MCP first, REST fallback only when empty
- Do not commit `.env`

## Tests

- `tests/test_health.py` — health, MCP, UI smoke
- `tests/test_incidents.py` — investigate wiring, chaos, legacy aliases
- Mock external services in unit tests; deep health may hit network if run live

## Docs

- Human docs: `README.md`, `docs/`
- Agent docs: `.agent/`
