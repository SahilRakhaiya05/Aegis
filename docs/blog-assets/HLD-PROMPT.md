# Aegis High-Level Design — Image Prompt

Use this prompt in Midjourney, DALL·E, Ideogram, Leonardo, or similar tools if you want a fresh graphic redesign. The product facts below must stay accurate.

---

## Master prompt (copy all)

Create a clean, modern software architecture high-level design diagram for a product called Aegis. White and light gray background, professional product-engineering style, not cyberpunk. Title at the top in bold dark navy: AEGIS — HIGH LEVEL DESIGN (HLD). Subtitle: SRE Copilot for Root Cause Analysis using SigNoz Observability, OpenTelemetry and Dual MCP.

Layout has five horizontal layers with rounded cards and soft shadows:

Layer 1 left, blue accent, APPLICATION LAYER: Aegis FastAPI Service, service.name = aegis. List endpoints: Health, Workload Orders, Chaos Error, Chaos Latency, Chaos Flaky, Storm, Investigate, Evidence, Aegis MCP POST /mcp. Side box Instrumentation OpenTelemetry Traces Logs Metrics exporting OTLP.

Layer 2 center-left, purple accent, OBSERVABILITY LAYER: SigNoz Cloud us2. Boxes for OTLP Ingest ingest.us2.signoz.cloud with signoz-ingestion-key, SigNoz Backend Traces Logs Metrics Dashboards Alerts, and Evidence APIs SigNoz MCP plus Query Range API fallback. Not self-hosted ClickHouse.

Layer 3 center-right, green accent, INVESTIGATION LAYER: Aegis Investigation Service pipeline numbered 1 to 7: SigNoz MCP Client, Evidence Collector, Evidence Correlator, Prompt Builder, Reasoner online or offline, Enrichment severity timeline playbook, Response Processor JSON validate. No Amazon Bedrock.

Layer 4 below observability, orange accent, AEGIS MCP: POST /mcp tools aegis_health aegis_investigate aegis_evidence aegis_fault aegis_history aegis_signoz_links. Label SigNoz MCP equals evidence, Aegis MCP equals actions.

Layer 5 far right, blue card, INCIDENT REPORT OUTPUT: Summary, Affected Service, Root Cause, Impact, Suggested Resolution, Confidence, Severity Score, Timeline, Playbook, Export MD JSON.

Bottom strip END-TO-END WORKFLOW with 10 numbered steps: Incident Occurs, Telemetry Generated, OTLP to SigNoz Cloud, Stored and Queryable, Probe Triggered, Evidence via SigNoz MCP, Context Built, Reasoner RCA, Enrich and Validate, Report Returned.

Bottom three panels: DEPLOYMENT local uvicorn and Docker container aegis, KEY FEATURES checklist, TECHNOLOGIES FastAPI OpenTelemetry SigNoz Cloud SigNoz MCP Aegis MCP Python Docker pytest.

Use crisp sans-serif labels, thin arrows with short captions OTLP MCP RCA, generous whitespace, flat icons, no clutter, 16:9 or wide landscape, presentation quality.

---

## Negative prompt (if the tool supports it)

cyberpunk neon, dark matrix, Amazon Bedrock, AWS EC2, self-hosted ClickHouse, AI Incident Investigator, blurry text, messy arrows, watermark, 3D plastic icons, cartoon mascot

---

## Short prompt (if character limit)

Wide clean HLD architecture diagram for Aegis SRE copilot on white background: FastAPI app aegis with chaos and investigate APIs, OpenTelemetry OTLP to SigNoz Cloud, SigNoz MCP evidence, Aegis MCP agent tools, reasoner online offline, RCA report with severity timeline playbook, 10-step workflow footer, deployment and tech stack panels, blue purple green orange cards, professional SaaS architecture style, sharp readable text

---

## What changed vs the old example

| Old example | Aegis version |
|-------------|---------------|
| AI Incident Investigator | Aegis |
| Amazon Bedrock | Reasoner (online / offline) |
| Self-hosted SigNoz + ClickHouse | SigNoz Cloud (us2) |
| Only Query API | SigNoz MCP first + Query fallback |
| No agent MCP | Aegis MCP (/mcp) with aegis_* tools |
| Basic report fields | + Severity, Timeline, Playbook, Export |
| EC2 IAM role story | Local / Docker + .env secrets |

---

## Generated file (ready to use)

`aegis-high-level-design.png` (project root)  
`docs/blog-assets/aegis-high-level-design.png`
