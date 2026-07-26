# Aegis — System Design

## 1. Overview

**Aegis** is an SRE copilot that turns SigNoz observability data into structured root-cause analysis (RCA) reports.

Stack:

- **FastAPI** — HTTP API, desk UI, Aegis MCP
- **OpenTelemetry** — traces, metrics, logs
- **SigNoz Cloud** — storage, explorers, hosted MCP
- **Reasoner** — online model when keys are set, otherwise offline structured fallback
- **Docker** — optional container run

Service name in telemetry: **`aegis`**.

---

## 2. Problem

Observability platforms store rich signals, but on-call still means manual correlation:

1. Find failing requests  
2. Open traces  
3. Search logs  
4. Align timestamps  
5. Form a hypothesis  
6. Decide remediation  

Aegis shortens that path to: **signals → evidence → RCA report**.

---

## 3. Goals

1. Instrument a demo workload with OpenTelemetry.  
2. Export telemetry to SigNoz Cloud over OTLP.  
3. Collect evidence via **SigNoz MCP** (REST query fallback).  
4. Produce structured RCA reports (severity, timeline, playbook).  
5. Expose **Aegis MCP** so agents can run the same flows.  
6. Provide a white desk UI for demos.  
7. Stay usable offline when no reasoner key is configured.

---

## 4. High-level architecture

```text
                    ┌─────────────────────┐
                    │   Engineer / Agent  │
                    └──────────┬──────────┘
           HTTP UI/API / MCP   │
                    ┌──────────▼──────────┐
                    │       Aegis         │
                    │  FastAPI + desk UI  │
                    │  Aegis MCP (/mcp)   │
                    │  Investigation svc  │
                    └─────┬─────────┬─────┘
                          │         │
              OTEL OTLP   │         │ SigNoz MCP
                          ▼         ▼
                    ┌─────────────────────┐
                    │    SigNoz Cloud     │
                    │ traces·logs·metrics │
                    │ dashboards·alerts   │
                    └─────────────────────┘
```

---

## 5. Components

| Component | Responsibility |
|-----------|----------------|
| Desk UI (`app/web`) | Human demo surface |
| REST API (`app/api`) | Probe, faults, workload, health |
| Aegis MCP (`app/mcp`) | Agent tools (`aegis_*`) |
| Evidence service | SigNoz MCP + Query API |
| Investigation service | Prompt + reasoner + enrichment |
| Observability | OTEL export to Cloud ingest |
| Workload / chaos | Controllable demo failures |

---

## 6. Data flows

### 6.1 Telemetry

```text
HTTP request → middleware span
            → app logs / metrics
            → OTLP HTTP + signoz-ingestion-key
            → SigNoz Cloud (service.name = aegis)
```

### 6.2 Investigation

```text
POST /api/v1/investigate
  → collect evidence (SigNoz MCP preferred)
  → reasoner (online | offline)
  → enrich (severity, timeline, playbook, links)
  → history + JSON report
```

### 6.3 Aegis MCP

```text
POST /mcp  tools/call  aegis_investigate
  → same investigation service as REST
```

---

## 7. Evidence model

| Signal | Source |
|--------|--------|
| Error traces | SigNoz MCP search / query |
| Error logs | SigNoz MCP search / query |
| Alerts | SigNoz MCP list alerts |
| Latency | Query API when available |
| Services | Optional MCP list |

Report extras:

- `severity` `{ score, label }`
- `timeline[]`
- `trace_ids[]`
- `playbook[]`
- `signoz_links` / `signoz_queries`

---

## 8. Reasoner

| Mode | When |
|------|------|
| Online | Reasoner API key present in env |
| Offline | No key — deterministic structured RCA |

UI never brands model vendors; it shows **online / offline** only.

---

## 9. Deployment

### Local

```text
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Docker

```text
docker compose up --build
```

Container: `aegis`. No local SigNoz compose network required when using Cloud.

---

## 10. Security notes

- Secrets only in `.env` (gitignored).  
- Prefer least-privilege SigNoz service accounts.  
- Rotate keys if exposed.  
- Aegis MCP is local-process scoped (no multi-tenant auth in this version).

---

## 11. Non-goals (current version)

- Full multi-tenant SaaS  
- Replacing SigNoz UI  
- Hard dependency on a single cloud LLM brand  

---

## 12. Related docs

- `README.md` — quick start & API  
- `.agent/` — agent workspace  
- `docs/aegis.md` — product guide  
- `docs/set-up.md` — setup  
- `demo/README.md` — demo scripts  
