"""Aegis High-Level Design diagram — remade from legacy HLD example."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent / "aegis-high-level-design.png"
OUT_DIR = Path(__file__).resolve().parents[2]


def fnt(size, bold=False):
    paths = (
        [r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\arialbd.ttf"]
        if bold
        else [r"C:\Windows\Fonts\segoeui.ttf", r"C:\Windows\Fonts\arial.ttf"]
    )
    for p in paths + [r"C:\Windows\Fonts\calibri.ttf"]:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def rr(d, box, r, fill, outline, w=2):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=w)


def text(d, xy, s, font, fill):
    d.text(xy, s, font=font, fill=fill)


def pill(d, x, y, w, h, label, fill, font, tfill=(255, 255, 255)):
    rr(d, (x, y, x + w, y + h), 8, fill, fill, 1)
    bbox = d.textbbox((0, 0), label, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    d.text((x + (w - tw) / 2, y + (h - th) / 2 - 1), label, font=font, fill=tfill)


# Palette
BG = (250, 250, 252)
INK = (15, 23, 42)
MUTE = (100, 116, 139)
WHITE = (255, 255, 255)
LINE = (226, 232, 240)
BLUE = (37, 99, 235)
BLUE_BG = (239, 246, 255)
PURPLE = (124, 58, 237)
PURPLE_BG = (245, 243, 255)
GREEN = (5, 150, 105)
GREEN_BG = (236, 253, 245)
ORANGE = (217, 119, 6)
ORANGE_BG = (255, 247, 237)
COPPER = (180, 83, 9)
TEAL = (13, 148, 136)

W, H = 1800, 1280
img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

title = fnt(34, True)
sub = fnt(18)
h2 = fnt(16, True)
body = fnt(14)
small = fnt(12)
tiny = fnt(11)

# Title
text(d, (48, 28), "AEGIS  —  HIGH LEVEL DESIGN (HLD)", title, INK)
text(
    d,
    (48, 72),
    "SRE Copilot for Root Cause Analysis using SigNoz Observability, OpenTelemetry & Dual MCP",
    sub,
    MUTE,
)

# ========== Layer 1: Application ==========
rr(d, (40, 120, 480, 560), 16, BLUE_BG, BLUE, 2)
pill(d, 56, 136, 200, 28, "1. APPLICATION LAYER", BLUE, small)
text(d, (56, 176), "Aegis FastAPI Service", h2, INK)
text(d, (56, 198), "service.name = aegis", small, MUTE)

# Endpoints card
rr(d, (56, 230, 300, 480), 12, WHITE, LINE, 1)
text(d, (72, 244), "API Endpoints", small, MUTE)
eps = [
    ("Health", "GET /api/v1/health"),
    ("Orders", "POST /api/v1/workload/orders"),
    ("Chaos Error", "GET /api/v1/chaos/error"),
    ("Chaos Latency", "GET /api/v1/chaos/latency"),
    ("Chaos Flaky", "GET /api/v1/chaos/flaky"),
    ("Storm", "POST /api/v1/chaos/storm"),
    ("Investigate", "POST /api/v1/investigate"),
    ("Evidence", "POST /api/v1/investigate/evidence"),
    ("Aegis MCP", "POST /mcp"),
]
for i, (a, b) in enumerate(eps):
    y = 270 + i * 22
    text(d, (72, y), f"• {a}", body, INK)
    text(d, (168, y), b, tiny, MUTE)

# OTEL box
rr(d, (316, 230, 460, 420), 12, WHITE, LINE, 1)
text(d, (330, 248), "Instrumentation", small, MUTE)
text(d, (330, 280), "OpenTelemetry", body, INK)
text(d, (330, 310), "• Traces", body, MUTE)
text(d, (330, 334), "• Logs", body, MUTE)
text(d, (330, 358), "• Metrics", body, MUTE)
text(d, (330, 390), "OTLP HTTP :443", small, TEAL)

# User icon area
text(d, (56, 510), "User / Engineer / Agent", body, MUTE)
text(d, (56, 532), "Desk UI  ·  REST  ·  MCP clients", small, MUTE)

# Arrow to layer 2
d.line((480, 300, 520, 300), fill=TEAL, width=3)
d.polygon([(520, 300), (508, 294), (508, 306)], fill=TEAL)
text(d, (485, 275), "OTLP", tiny, TEAL)

# ========== Layer 2: Observability ==========
rr(d, (530, 120, 980, 420), 16, PURPLE_BG, PURPLE, 2)
pill(d, 546, 136, 280, 28, "2. OBSERVABILITY LAYER", PURPLE, small)
text(d, (546, 180), "SigNoz Cloud (us2)", h2, INK)
text(d, (546, 202), "improved-moose.us2.signoz.cloud", small, MUTE)

rr(d, (546, 240, 750, 340), 10, WHITE, LINE, 1)
text(d, (560, 255), "OTLP Ingest", body, INK)
text(d, (560, 280), "ingest.us2.signoz.cloud", tiny, MUTE)
text(d, (560, 300), "signoz-ingestion-key", tiny, MUTE)

rr(d, (770, 240, 960, 340), 10, WHITE, LINE, 1)
text(d, (784, 255), "SigNoz Backend", body, INK)
text(d, (784, 280), "Traces · Logs · Metrics", tiny, MUTE)
text(d, (784, 300), "Dashboards · Alerts", tiny, MUTE)

rr(d, (546, 360, 960, 400), 10, WHITE, LINE, 1)
text(d, (560, 372), "Evidence APIs:  SigNoz MCP  +  Query Range API (fallback)", body, MUTE)

# Arrow to layer 3
d.line((980, 280, 1020, 280), fill=GREEN, width=3)
d.polygon([(1020, 280), (1008, 274), (1008, 286)], fill=GREEN)
text(d, (985, 255), "MCP", tiny, GREEN)

# ========== Layer 3: Investigation ==========
rr(d, (1030, 120, 1460, 520), 16, GREEN_BG, GREEN, 2)
pill(d, 1046, 136, 300, 28, "3. INVESTIGATION LAYER", GREEN, small)
text(d, (1046, 176), "Aegis Investigation Service", h2, INK)

steps = [
    "1. SigNoz MCP Client (API key + X-SigNoz-URL)",
    "2. Evidence Collector (traces · logs · alerts)",
    "3. Evidence Correlator (window + service)",
    "4. Prompt Builder (structured RCA prompt)",
    "5. Reasoner (online | offline)",
    "6. Enrichment (severity · timeline · playbook)",
    "7. Response Processor (validate JSON report)",
]
for i, s in enumerate(steps):
    y = 210 + i * 36
    rr(d, (1046, y, 1440, y + 30), 8, WHITE, LINE, 1)
    text(d, (1060, y + 6), s, body, INK)

# ========== Layer 4: Aegis MCP ==========
rr(d, (530, 440, 980, 620), 16, ORANGE_BG, ORANGE, 2)
pill(d, 546, 456, 200, 28, "4. AEGIS MCP", ORANGE, small)
text(d, (546, 500), "POST /mcp  ·  AegisMCP server", h2, INK)
tools = "aegis_health · aegis_investigate · aegis_evidence · aegis_fault · aegis_history · aegis_signoz_links"
text(d, (546, 530), tools, small, MUTE)
text(d, (546, 560), "Agents / IDEs call the same investigation backend as the desk UI", small, MUTE)
text(d, (546, 590), "SigNoz MCP = evidence   |   Aegis MCP = actions", body, COPPER)

# ========== Layer 5: Report ==========
rr(d, (1500, 200, 1760, 520), 16, BLUE_BG, BLUE, 2)
pill(d, 1516, 216, 220, 28, "5. INCIDENT REPORT", BLUE, small)
outs = [
    "Summary",
    "Affected Service",
    "Root Cause",
    "Impact",
    "Suggested Resolution",
    "Confidence",
    "Severity Score",
    "Timeline",
    "Playbook",
    "Export MD / JSON",
]
for i, o in enumerate(outs):
    text(d, (1520, 260 + i * 24), f"✓  {o}", body, INK)

d.line((1460, 340, 1500, 340), fill=BLUE, width=3)
d.polygon([(1500, 340), (1488, 334), (1488, 346)], fill=BLUE)

# ========== Workflow strip ==========
rr(d, (40, 650, 1760, 860), 14, WHITE, LINE, 2)
pill(d, 56, 666, 180, 26, "END-TO-END WORKFLOW", INK, small)
wf = [
    ("1", "Incident\nOccurs"),
    ("2", "Telemetry\nGenerated"),
    ("3", "OTLP to\nSigNoz Cloud"),
    ("4", "Stored &\nQueryable"),
    ("5", "Probe\nTriggered"),
    ("6", "Evidence via\nSigNoz MCP"),
    ("7", "Context\nBuilt"),
    ("8", "Reasoner\nRCA"),
    ("9", "Enrich &\nValidate"),
    ("10", "Report\nReturned"),
]
for i, (n, label) in enumerate(wf):
    x = 70 + i * 168
    d.ellipse((x + 40, 710, x + 72, 742), fill=BLUE if i < 5 else GREEN)
    center = (x + 40, 710, x + 72, 742)
    bbox = d.textbbox((0, 0), n, font=small)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    d.text((x + 56 - tw / 2, 716), n, font=small, fill=WHITE)
    for j, line in enumerate(label.split("\n")):
        text(d, (x + 20, 756 + j * 18), line, tiny, MUTE)
    if i < 9:
        d.line((x + 90, 726, x + 155, 726), fill=LINE, width=2)

# ========== Bottom panels ==========
rr(d, (40, 880, 560, 1240), 14, WHITE, LINE, 2)
pill(d, 56, 896, 200, 26, "DEPLOYMENT", INK, small)
text(d, (56, 940), "Local / Docker", h2, INK)
text(d, (56, 970), "uvicorn app.main:app :8000", body, MUTE)
text(d, (56, 1000), "Optional: docker compose up --build", body, MUTE)
text(d, (56, 1040), "SigNoz Cloud (no local ClickHouse required)", body, INK)
text(d, (56, 1070), "• OTLP → ingest.us2.signoz.cloud:443", small, MUTE)
text(d, (56, 1094), "• MCP → mcp.us2.signoz.cloud/mcp", small, MUTE)
text(d, (56, 1118), "• UI → http://127.0.0.1:8000/", small, MUTE)
text(d, (56, 1150), "Container name: aegis", body, TEAL)
text(d, (56, 1180), "Secrets: .env only (never commit)", small, MUTE)

rr(d, (580, 880, 1140, 1240), 14, WHITE, LINE, 2)
pill(d, 596, 896, 160, 26, "KEY FEATURES", INK, small)
features = [
    "End-to-end observability (traces, logs, metrics)",
    "SigNoz MCP–first evidence collection",
    "Aegis MCP for agents (aegis_* tools)",
    "Structured RCA with severity & timeline",
    "Playbook + Markdown/JSON export",
    "Chaos injectors & demo workload faults",
    "Offline reasoner fallback for reliable demos",
    "Deep links back into SigNoz explorers",
    "White desk UI for human operators",
]
for i, feat in enumerate(features):
    text(d, (596, 940 + i * 28), f"✓  {feat}", body, INK)

rr(d, (1160, 880, 1760, 1240), 14, WHITE, LINE, 2)
pill(d, 1176, 896, 200, 26, "TECHNOLOGIES", INK, small)
techs = [
    ("FastAPI", "Application & API"),
    ("OpenTelemetry", "Instrumentation"),
    ("SigNoz Cloud", "Observability backend"),
    ("SigNoz MCP", "Evidence tools"),
    ("Aegis MCP", "Agent investigation tools"),
    ("Python 3.11+", "Runtime"),
    ("Docker", "Packaging"),
    ("pytest", "Test suite"),
]
for i, (a, b) in enumerate(techs):
    y = 940 + i * 30
    text(d, (1176, y), a, body, INK)
    text(d, (1380, y), b, small, MUTE)

text(d, (1176, 1200), "Reasoner: online when keys set · offline otherwise", small, COPPER)

img.save(OUT, "PNG")
# also copy to project root with clean name
root_out = OUT_DIR / "aegis-high-level-design.png"
img.save(root_out, "PNG")
print("wrote", OUT)
print("wrote", root_out)
