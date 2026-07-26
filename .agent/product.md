# Aegis product brief

## One-liner

Aegis is an SRE copilot that turns SigNoz telemetry into structured root-cause reports.

## Audience

- Engineers debugging production incidents
- Agents/IDEs calling Aegis MCP
- Demo reviewers evaluating SigNoz + MCP integration

## Jobs to be done

1. **Ingest** — export OTEL traces/logs/metrics to SigNoz Cloud.
2. **Inject** — optional fault injectors for demos.
3. **Collect** — pull error traces, logs, alerts via SigNoz MCP.
4. **Reason** — produce structured RCA (online reasoner or offline fallback).
5. **Expose** — Aegis MCP tools so external agents can run the same flows.
6. **Present** — white desk UI for humans.
7. **Score** — severity scoring, evidence timeline, playbook steps.
8. **Export** — copy/JSON/Markdown report export for demos and handoff.

## Out of scope

- Replacing SigNoz UI
- Multi-tenant SaaS auth (local/demo focus)
- Shipping vendor-branded model marketing in the UI
