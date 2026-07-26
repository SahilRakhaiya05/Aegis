# Aegis: Turning SigNoz Telemetry into Actionable Root-Cause Analysis

**How we built an SRE copilot that connects OpenTelemetry, SigNoz Cloud, and MCP into one investigation workflow.**

---

## Introduction

If you’ve ever been on-call, you know this feeling.

An alert fires. Slack lights up. Someone drops a dashboard link. You open SigNoz (or Grafana, or Datadog), and suddenly you’re staring at a wall of traces, logs, and metrics — all useful, none of them telling you the full story in one place.

You start the familiar dance:

- find the failing request  
- open the trace  
- jump to logs  
- compare timestamps  
- check if latency spiked  
- guess the root cause  
- hope you’re right  

Observability platforms are excellent at **storing** signals. They’re less excellent at **explaining** incidents under pressure.

That’s the gap we set out to close with **Aegis**.

Aegis is an SRE copilot built on top of **SigNoz**. It collects correlated evidence from your telemetry, runs a reasoner over that evidence, and returns a structured root-cause report you can actually act on — complete with severity, timeline, playbook steps, and deep links back into SigNoz.

This post walks through:

- the problem we cared about  
- what Aegis does  
- architecture and tech stack  
- how evidence flows through SigNoz MCP  
- the dual-MCP design (SigNoz + Aegis)  
- a real demo path  
- what we learned building it  

---

## The problem: data-rich, answer-poor

Modern systems emit more telemetry than any human can read during a five-minute outage.

A single request failure can produce:

- dozens of spans across services  
- stack traces and ERROR logs  
- metric spikes in latency and error rate  
- related alerts  

The raw data is there. The bottleneck is **cognitive load**.

What on-call engineers need is not more panels. They need a short, trustworthy narrative:

1. What broke?  
2. What is the most likely cause?  
3. Who/what was impacted?  
4. What should we do next?  

Aegis is our answer to that workflow.

---

## What is Aegis?

**Aegis** is an incident investigation desk for teams using SigNoz.

At a high level:

```text
Live traffic / fault injectors
        │
        ▼
OpenTelemetry (traces · logs · metrics)
        │  OTLP → SigNoz Cloud
        ▼
SigNoz (storage + explorers + MCP)
        │
        ▼
Aegis investigation pipeline
        │
        ├─ evidence collection (SigNoz MCP first)
        ├─ reasoner (online or offline)
        └─ enrichment (severity, timeline, playbook)
                │
                ▼
Structured RCA report
   (UI · REST API · Aegis MCP)
```

### What you get after a probe

A typical Aegis report includes:

| Field | Meaning |
|-------|---------|
| **Summary** | What happened, in plain language |
| **Root cause** | Best-supported hypothesis from evidence |
| **Impact** | Who/what was affected |
| **Suggested resolution** | Concrete next steps |
| **Confidence** | high / medium / low |
| **Severity** | scored label (low → critical) |
| **Timeline** | ordered trace/log/alert events |
| **Playbook** | checklist for the next 10 minutes |
| **Evidence source** | e.g. `signoz_mcp` |
| **Exports** | Markdown / JSON / copy |

Aegis is not trying to replace SigNoz.  
It sits **on top** of SigNoz and makes investigation faster.

---

## Design principles

We made a few deliberate product choices early:

### 1. Evidence first, model second
The reasoner only sees evidence collected from SigNoz. If there are no error traces or logs in the window, Aegis says so — it doesn’t invent a root cause.

### 2. MCP as a first-class interface
We use **SigNoz MCP** for evidence collection, and we expose **Aegis MCP** so agents and IDEs can run the same investigation tools humans use in the UI.

### 3. Demo reliability
If no model API key is configured, Aegis still completes probes in **offline** mode. The pipeline remains testable and demoable.

### 4. Human language in the UI
The UI talks about **probes**, **faults**, **severity**, and **reasoner online/offline** — not vendor model branding.

### 5. Always link back to SigNoz
Every serious investigation should end in the source of truth. Reports include deep links and query snippets for traces/logs.

---

## Tech stack

| Layer | Choice | Why |
|-------|--------|-----|
| API & app | **FastAPI** | Fast to ship, clean async endpoints, great OpenAPI docs |
| Telemetry | **OpenTelemetry** | Standard instrumentation; works natively with SigNoz |
| Observability backend | **SigNoz Cloud** | Traces, logs, metrics, alerts in one place |
| Evidence API | **SigNoz MCP** + Query Range API | MCP-first; REST fallback |
| Agent interface | **Aegis MCP** (`/mcp`) | Same tools for agents and automation |
| Reasoner | Multi-backend router | Online when keys exist; offline otherwise |
| UI | Lightweight HTML/CSS/JS desk | Fast demo surface, white “paper desk” aesthetic |
| Packaging | Docker + `uvicorn` | Easy local and container runs |
| Tests | **pytest** | Health, MCP, enrichment, workload coverage |

Service name in telemetry: **`aegis`**.

---

## Architecture (in depth)

### 1) Application surface

Aegis exposes three surfaces:

1. **Desk UI** (`/`) — human investigation workspace  
2. **REST API** (`/api/v1/...`) — scripts, integrations, demos  
3. **Aegis MCP** (`POST /mcp`) — tools for agents  

All three call the same core services. That matters: one investigation path, many front doors.

### 2) Observability path

Every request can produce:

- HTTP server spans (custom middleware)  
- application logs (exported via OTEL log pipeline)  
- business metrics (orders, chaos events, investigations)  

These export over **OTLP HTTP/protobuf** to SigNoz Cloud ingest with an ingestion key header.

That means when you click a fault injector in the UI, you’re not faking a dashboard — you’re generating real telemetry.

### 3) Evidence collection

When you run a probe for service `aegis` over the last N minutes, Aegis:

1. Queries **SigNoz MCP** for error traces  
2. Queries error logs  
3. Optionally lists firing alerts  
4. Optionally enriches with trace details  
5. Falls back to REST Query Range only if core evidence is empty  

This MCP-first design is important in practice. Depending on key permissions, some environments authorize MCP and version endpoints more cleanly than raw query APIs. Aegis is designed around that reality.

### 4) Reasoning + enrichment

After evidence is collected:

1. Evidence is packaged into a JSON context  
2. A reasoner produces structured RCA fields  
3. Enrichment adds:
   - severity score/label  
   - timeline events  
   - trace IDs  
   - playbook steps  
   - SigNoz deep links and query snippets  

This split keeps the model focused on explanation, while deterministic code handles scoring and navigation.

### 5) Dual MCP design

This is one of the most interesting parts of Aegis.

| MCP | Role |
|-----|------|
| **SigNoz MCP** | Read observability data (traces, logs, alerts, services…) |
| **Aegis MCP** | Run Aegis workflows (investigate, evidence, faults, history…) |

Example Aegis MCP tools:

- `aegis_health`  
- `aegis_investigate`  
- `aegis_evidence`  
- `aegis_history`  
- `aegis_fault`  
- `aegis_signoz_links`  

So an agent can do things like:

> “Investigate service `aegis` for the last 30 minutes.”

…and call the same backend path the UI uses.

---

## A walk through a real investigation

Here’s the happy path we use in demos.

### Step 1: Confirm connectivity

Open the desk and check:

- SigNoz API is up  
- SigNoz MCP is connected (tool count visible)  
- Aegis MCP is ready  

If these are green, you’re ready.

### Step 2: Generate an incident

You can:

- use **Full dry-run** in the UI  
- inject faults manually (500 / latency / flaky / storm)  
- place risky orders (quantity > 100 has an intentional inventory timeout)  
- run `demo/generate_incident.ps1` or `demo/generate_incident.sh`  

These actions create real OTEL signals under service **`aegis`**.

### Step 3: Wait for Cloud ingestion

SigNoz Cloud usually needs a short window (often ~10–30 seconds) before new spans/logs are queryable.

### Step 4: Run a probe

Aegis collects evidence and returns a report.

What “good” looks like:

- `evidence_source`: `signoz_mcp` (or `hybrid`)  
- non-empty error traces and/or logs  
- severity label present  
- timeline populated  
- playbook steps generated  

### Step 5: Verify in SigNoz

Open SigNoz:

- **Services** → `aegis`  
- **Traces** → filter error spans  
- **Logs** → ERROR/FATAL for the service  

This closes the loop: Aegis explains; SigNoz proves.

### Step 6: Export or hand off

From the report you can:

- copy JSON  
- export Markdown  
- open Traces deep link  
- share playbook steps with the team  

---

## UI philosophy: an incident desk, not a landing page

We intentionally designed the UI like an operations desk:

- white “paper” background  
- clear navigation: Home · Probe · Faults · MCP · SigNoz  
- status cards first  
- report with severity badge  
- timeline + playbook under the narrative  
- keyboard shortcut (`Ctrl+Enter`) to run a probe  

The UI avoids marketing fluff. It answers:

- Are we connected?  
- What should I run?  
- What did we find?  
- What do I do next?  

That focus makes demos clearer and day-to-day use less noisy.

---

## Project structure (for readers who want to dig in)

```text
app/
  bootstrap.py / main.py / settings.py
  domain/                 # models
  integrations/
    signoz/               # query API, MCP client, links
    llm/                  # reasoner router
  mcp/                    # Aegis MCP server
  observability/          # OTEL exporters + metrics
  services/               # evidence, investigation, chaos, workload
  api/routes/             # REST
  web/                    # desk UI
demo/                     # traffic generators
docs/                     # human docs + this blog
.agent/                   # agent workspace / runbooks
tests/                    # pytest suite
```

This layout keeps business logic in `services/`, integrations isolated, and both REST + MCP thin on top.

---

## Challenges we hit (and how we handled them)

### 1) “Failed to fetch” in the browser
Almost always means the API process isn’t running.  
We added clearer UI errors and a `start.ps1` launcher so demos recover faster.

### 2) MCP vs REST permissions
Some keys work beautifully with SigNoz MCP but fail on raw query endpoints.  
Aegis prefers MCP and only falls back when needed.

### 3) Cloud ingestion delay
Immediate probe after fault injection can return empty evidence.  
Dry-run and demo scripts intentionally wait before investigating.

### 4) Model dependency risk
If the reasoner is unavailable, offline mode still returns a structured report so the product remains demo-safe.

### 5) Naming and product clarity
We rebranded fully to **Aegis**, separated **SigNoz MCP** from **Aegis MCP**, and removed confusing legacy names from docs and demos.

---

## What we learned

### Observability is necessary, not sufficient
Dashboards don’t reduce MTTR by themselves. Workflows do.

### Shared backends beat duplicated logic
UI, REST, and Aegis MCP all call the same investigation services. That keeps behavior consistent for humans and agents.

### MCP is most valuable when it’s operational
“MCP support” only matters if tools map to real workflows: investigate, fetch evidence, inject faults, export context.

### Reliability is a product feature
Offline reasoner mode, deep health checks, and explicit empty-evidence handling made the system trustworthy.

### Good demos need design
A clean white desk, severity badges, timeline, and export buttons make the value obvious in under two minutes.

---

## What’s next

A few directions we’re excited about:

1. **Multi-service correlation** across dependency chains  
2. **Alert-triggered auto-probes** (alert fires → Aegis investigates)  
3. **Richer SLO context** in reports (error budget impact)  
4. **Persistent investigation history** beyond process memory  
5. **Tighter agent loops** where Aegis MCP + SigNoz MCP collaborate step-by-step  

---

## Try it yourself

### Run locally

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# add SigNoz URL, API key, OTLP ingestion headers
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Or:

```powershell
.\start.ps1
```

### Demo scripts

```powershell
.\demo\generate_incident.ps1
```

```bash
./demo/generate_incident.sh
```

### Useful URLs

- UI: `http://127.0.0.1:8000/`  
- Health: `http://127.0.0.1:8000/api/v1/health/deep`  
- OpenAPI: `http://127.0.0.1:8000/docs`  
- Aegis MCP: `POST http://127.0.0.1:8000/mcp`  

### GitHub

If you’re following along with our open repository:

**https://github.com/SahilRakhaiya05/Aegis**

---

## Closing

Aegis started from a simple observation: during incidents, engineers don’t need more charts — they need faster understanding.

By combining:

- OpenTelemetry instrumentation  
- SigNoz Cloud as the system of record  
- SigNoz MCP for evidence  
- Aegis MCP for agent workflows  
- a focused investigation desk  

…we built a path from **failure → evidence → root cause → next action**.

If you’re already on SigNoz, this pattern is available today: instrument your service, export OTLP, query via MCP, and put an investigation layer on top.

That’s Aegis.

---

### Suggested publish metadata

| Field | Suggestion |
|-------|------------|
| **Title** | Aegis: Turning SigNoz Telemetry into Actionable Root-Cause Analysis |
| **Subtitle** | Building an SRE copilot with OpenTelemetry, SigNoz MCP, and agent-ready tools |
| **Tags** | SigNoz, OpenTelemetry, Observability, MCP, SRE, FastAPI, Incident Response |
| **Series angle** | Observability engineering / AI-assisted ops |
| **Cover idea** | Clean white desk UI screenshot + SigNoz traces side-by-side |

### Optional pull-quotes for social

> “Observability stores the signals. Aegis turns them into a story you can act on.”

> “UI, REST, and Aegis MCP all share one investigation backend — humans and agents get the same truth.”

---

*Written for engineers who live in traces and still want better answers at 2 a.m.*
