# Aegis: Turning SigNoz Telemetry into Actionable Root-Cause Analysis

How we built an SRE copilot that connects OpenTelemetry, SigNoz Cloud, and MCP into one investigation workflow.

---

Hello everyone.

If you have ever been on-call, you already know this feeling.

An alert fires. Slack lights up. Someone drops a dashboard link. You open SigNoz, and suddenly you are staring at a wall of traces, logs, and metrics. All of them are useful. None of them tell you the full story in one place.

You start the familiar dance:

• find the failing request  
• open the trace  
• jump to logs  
• compare timestamps  
• check if latency spiked  
• guess the root cause  
• hope you are right  

Observability platforms are excellent at storing signals. They are less excellent at explaining incidents under pressure.

That is the gap we set out to close with Aegis.

Aegis is an SRE copilot built on top of SigNoz. It collects correlated evidence from your telemetry, runs a reasoner over that evidence, and returns a structured root-cause report you can actually act on — complete with severity, timeline, playbook steps, and deep links back into SigNoz.

In this post, we will walk through:

• the problem we cared about  
• what Aegis does  
• architecture and tech stack  
• how evidence flows through SigNoz MCP  
• the dual-MCP design (SigNoz + Aegis)  
• a real demo path  
• what we learned building it  

---

## The problem: data-rich, answer-poor

Modern systems emit more telemetry than any human can read during a five-minute outage.

A single request failure can produce:

• dozens of spans across services  
• stack traces and ERROR logs  
• metric spikes in latency and error rate  
• related alerts  

The raw data is there. The bottleneck is cognitive load.

What on-call engineers need is not more panels. They need a short, trustworthy narrative:

1. What broke?  
2. What is the most likely cause?  
3. Who or what was impacted?  
4. What should we do next?  

Aegis is our answer to that workflow.

---

## What is Aegis?

Aegis is an incident investigation desk for teams using SigNoz.

At a high level:

[IMAGE 1 — insert: docs/blog-assets/01-architecture.png]

Caption: Aegis sits between engineers/agents and SigNoz Cloud. Telemetry flows in through OpenTelemetry. Evidence comes back through SigNoz MCP. The output is a structured RCA report.

After a probe, a typical Aegis report includes:

• Summary — what happened, in plain language  
• Root cause — best-supported hypothesis from evidence  
• Impact — who or what was affected  
• Suggested resolution — concrete next steps  
• Confidence — high / medium / low  
• Severity — scored label from low to critical  
• Timeline — ordered trace, log, and alert events  
• Playbook — checklist for the next 10 minutes  
• Evidence source — for example signoz_mcp  
• Exports — Markdown, JSON, or copy  

Aegis is not trying to replace SigNoz.  
It sits on top of SigNoz and makes investigation faster.

---

## Design principles

We made a few deliberate product choices early.

1) Evidence first, model second  
The reasoner only sees evidence collected from SigNoz. If there are no error traces or logs in the window, Aegis says so. It does not invent a root cause.

2) MCP as a first-class interface  
We use SigNoz MCP for evidence collection, and we expose Aegis MCP so agents and IDEs can run the same investigation tools humans use in the UI.

3) Demo reliability  
If no model API key is configured, Aegis still completes probes in offline mode. The pipeline remains testable and demoable.

4) Human language in the UI  
The UI talks about probes, faults, severity, and reasoner online or offline — not vendor model branding.

5) Always link back to SigNoz  
Every serious investigation should end in the source of truth. Reports include deep links and query snippets for traces and logs.

---

## Before and after

[IMAGE 2 — insert: docs/blog-assets/04-before-after.png]

Caption: Manual investigation is a loop of dashboards and guesswork. With Aegis, the path becomes traffic, evidence, structured RCA, and clear next steps.

---

## Tech stack

Here is what we used and why.

• FastAPI — backend API, OpenAPI docs, async endpoints  
• OpenTelemetry — standard traces, logs, and metrics  
• SigNoz Cloud — store and explore all signals  
• SigNoz MCP — pull evidence with tool calls  
• Aegis MCP — agent-facing investigation tools at /mcp  
• Multi-backend reasoner — online when keys exist, offline otherwise  
• Lightweight HTML, CSS, and JS desk UI — fast demo surface  
• Docker and uvicorn — simple local and container runs  
• pytest — health, MCP, enrichment, and workload tests  

Service name in telemetry: aegis

---

## Architecture in depth

### Application surface

Aegis exposes three surfaces:

1. Desk UI at / — human investigation workspace  
2. REST API at /api/v1 — scripts, integrations, demos  
3. Aegis MCP at POST /mcp — tools for agents  

All three call the same core services. That matters. One investigation path. Many front doors.

### Observability path

Every request can produce:

• HTTP server spans  
• application logs  
• business metrics such as orders, chaos events, and investigations  

These export over OTLP HTTP/protobuf to SigNoz Cloud ingest with an ingestion key header.

That means when you click a fault injector in the UI, you are not faking a dashboard. You are generating real telemetry.

### Investigation pipeline

[IMAGE 3 — insert: docs/blog-assets/02-pipeline.png]

Caption: Five steps from inject to report — traffic, OTEL export, SigNoz MCP evidence, reasoner, enrichment.

When you run a probe for service aegis over the last N minutes, Aegis:

1. Queries SigNoz MCP for error traces  
2. Queries error logs  
3. Optionally lists firing alerts  
4. Optionally enriches with trace details  
5. Falls back to REST Query Range only if core evidence is empty  

This MCP-first design matters in practice. Depending on key permissions, some environments authorize MCP more cleanly than raw query APIs. Aegis is designed around that reality.

### Reasoning and enrichment

After evidence is collected:

1. Evidence is packaged into a JSON context  
2. A reasoner produces structured RCA fields  
3. Enrichment adds severity, timeline, trace IDs, playbook steps, and SigNoz links  

This split keeps the model focused on explanation, while deterministic code handles scoring and navigation.

---

## Dual MCP design

This is one of the most interesting parts of Aegis.

[IMAGE 4 — insert: docs/blog-assets/03-dual-mcp.png]

Caption: SigNoz MCP is for reading observability data. Aegis MCP is for running investigations and demo faults. Humans and agents share the same backend.

SigNoz MCP

• search traces and logs  
• list alerts and services  
• fetch trace details  
• run observability queries  

Aegis MCP

• aegis_investigate  
• aegis_evidence  
• aegis_fault  
• aegis_history  
• aegis_signoz_links  
• aegis_health  

So an agent can say:

Investigate service aegis for the last 30 minutes.

…and call the same backend path the UI uses.

---

## A walk through a real investigation

Here is the happy path we use in demos.

Step 1: Confirm connectivity  
Open the desk and check SigNoz API, SigNoz MCP, and Aegis MCP.

Step 2: Generate an incident  
Use Full dry-run in the UI, inject faults manually, place risky orders, or run the demo scripts under demo/.

Step 3: Wait for Cloud ingestion  
SigNoz Cloud usually needs a short window, often about 10 to 30 seconds, before new spans and logs are queryable.

Step 4: Run a probe  
Aegis collects evidence and returns a report.

What good looks like:

• evidence_source is signoz_mcp or hybrid  
• non-empty error traces and/or logs  
• severity label present  
• timeline populated  
• playbook steps generated  

Step 5: Verify in SigNoz  
Open Services for aegis, Traces with error spans, and Logs for ERROR or FATAL.  
This closes the loop. Aegis explains. SigNoz proves.

Step 6: Export or hand off  
Copy JSON, export Markdown, open Traces, or share playbook steps with the team.

---

## UI philosophy: an incident desk, not a landing page

We intentionally designed the UI like an operations desk:

• white paper background  
• clear navigation: Home, Probe, Faults, MCP, SigNoz  
• status cards first  
• report with severity badge  
• timeline and playbook under the narrative  
• keyboard shortcut Ctrl+Enter to run a probe  

The UI avoids marketing fluff. It answers:

• Are we connected?  
• What should I run?  
• What did we find?  
• What do I do next?  

That focus makes demos clearer and day-to-day use less noisy.

---

## Challenges we hit, and how we handled them

1) Failed to fetch in the browser  
Almost always means the API process is not running. We added clearer UI errors and a start.ps1 launcher so demos recover faster.

2) MCP versus REST permissions  
Some keys work beautifully with SigNoz MCP but fail on raw query endpoints. Aegis prefers MCP and only falls back when needed.

3) Cloud ingestion delay  
Immediate probe after fault injection can return empty evidence. Dry-run and demo scripts intentionally wait before investigating.

4) Model dependency risk  
If the reasoner is unavailable, offline mode still returns a structured report so the product remains demo-safe.

5) Naming and product clarity  
We branded fully as Aegis, separated SigNoz MCP from Aegis MCP, and removed confusing legacy names from docs and demos.

---

## What we learned

Observability is necessary, not sufficient.  
Dashboards do not reduce MTTR by themselves. Workflows do.

Shared backends beat duplicated logic.  
UI, REST, and Aegis MCP all call the same investigation services. That keeps behavior consistent for humans and agents.

MCP is most valuable when it is operational.  
MCP support only matters if tools map to real workflows: investigate, fetch evidence, inject faults, export context.

Reliability is a product feature.  
Offline reasoner mode, deep health checks, and explicit empty-evidence handling made the system trustworthy.

Good demos need design.  
A clean white desk, severity badges, timeline, and export buttons make the value obvious in under two minutes.

---

## What is next

A few directions we are excited about:

1. Multi-service correlation across dependency chains  
2. Alert-triggered auto-probes when alerts fire  
3. Richer SLO context in reports  
4. Persistent investigation history beyond process memory  
5. Tighter agent loops where Aegis MCP and SigNoz MCP collaborate step by step  

---

## Try it yourself

Run locally:

py -3.13 -m venv .venv  
.\.venv\Scripts\Activate.ps1  
pip install -r requirements.txt  
copy .env.example .env  
uvicorn app.main:app --host 127.0.0.1 --port 8000  

Or:

.\start.ps1  

Demo scripts:

.\demo\generate_incident.ps1  

./demo/generate_incident.sh  

Useful URLs:

• UI: http://127.0.0.1:8000/  
• Health: http://127.0.0.1:8000/api/v1/health/deep  
• OpenAPI: http://127.0.0.1:8000/docs  
• Aegis MCP: POST http://127.0.0.1:8000/mcp  

GitHub:

https://github.com/SahilRakhaiya05/Aegis  

---

## Closing

Aegis started from a simple observation: during incidents, engineers do not need more charts. They need faster understanding.

By combining OpenTelemetry instrumentation, SigNoz Cloud as the system of record, SigNoz MCP for evidence, Aegis MCP for agent workflows, and a focused investigation desk, we built a path from failure to evidence to root cause to next action.

If you are already on SigNoz, this pattern is available today: instrument your service, export OTLP, query via MCP, and put an investigation layer on top.

That is Aegis.

Thank you for reading.

---

## Medium publish checklist

Title  
Aegis: Turning SigNoz Telemetry into Actionable Root-Cause Analysis

Subtitle  
Building an SRE copilot with OpenTelemetry, SigNoz MCP, and agent-ready tools

Tags  
SigNoz, OpenTelemetry, Observability, MCP, SRE, FastAPI, Incident Response

Images to upload (in order)

1. docs/blog-assets/01-architecture.png  
2. docs/blog-assets/04-before-after.png  
3. docs/blog-assets/02-pipeline.png  
4. docs/blog-assets/03-dual-mcp.png  

How to publish on Medium

1. New story  
2. Paste this article  
3. Replace each [IMAGE …] line by uploading the matching PNG  
4. Add captions under each image  
5. Set cover image (architecture or before/after works well)  
6. Preview, then publish  

Social one-liners

Observability stores the signals. Aegis turns them into a story you can act on.

UI, REST, and Aegis MCP all share one investigation backend — humans and agents get the same truth.
