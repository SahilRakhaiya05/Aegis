# Aegis · agent workspace

Instructions and maps for coding agents working on this repository.

| Doc | Purpose |
|-----|---------|
| [product.md](product.md) | What Aegis is and is not |
| [architecture.md](architecture.md) | Package map and data flows |
| [mcp.md](mcp.md) | SigNoz MCP + Aegis MCP |
| [runbook.md](runbook.md) | Local run, demo, verify |
| [conventions.md](conventions.md) | Coding conventions |

## Non-negotiables

1. Product name is **Aegis**; OTEL service is **`aegis`**.
2. UI never shows vendor model brand names (Gemini/OpenAI/etc.) — only **online / offline**.
3. Secrets stay in `.env` (gitignored).
4. Prefer SigNoz MCP for evidence; do not remove Aegis MCP at `/mcp`.
5. Keep the desk UI light/white unless the user asks otherwise.
