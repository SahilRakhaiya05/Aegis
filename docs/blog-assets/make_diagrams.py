"""Generate Medium-ready architecture diagrams for the Aegis blog."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

out = Path(__file__).resolve().parent
out.mkdir(parents=True, exist_ok=True)


def font(size, bold=False):
    candidates = [
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
    ]
    bold_c = [
        r"C:\Windows\Fonts\segoeuib.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
    ]
    paths = bold_c if bold else candidates
    for p in paths + candidates:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


def rounded_rect(draw, xy, r, fill, outline=None, width=2):
    draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=width)


def center_text(draw, box, text, f, fill):
    x0, y0, x1, y1 = box
    bbox = draw.textbbox((0, 0), text, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((x0 + x1 - tw) / 2, (y0 + y1 - th) / 2), text, font=f, fill=fill)


def arrow(d, x1, y1, x2, y2, label=None, f=None, bg=(247, 246, 243), color=(179, 92, 46)):
    d.line((x1, y1, x2, y2), fill=color, width=3)
    if abs(x2 - x1) >= abs(y2 - y1):
        direction = 1 if x2 > x1 else -1
        d.polygon(
            [(x2, y2), (x2 - 12 * direction, y2 - 7), (x2 - 12 * direction, y2 + 7)],
            fill=color,
        )
    else:
        direction = 1 if y2 > y1 else -1
        d.polygon(
            [(x2, y2), (x2 - 7, y2 - 12 * direction), (x2 + 7, y2 - 12 * direction)],
            fill=color,
        )
    if label and f:
        mx, my = (x1 + x2) // 2, (y1 + y2) // 2
        bbox = d.textbbox((0, 0), label, font=f)
        tw = bbox[2] - bbox[0]
        d.rectangle((mx - tw // 2 - 8, my - 14, mx + tw // 2 + 8, my + 14), fill=bg)
        d.text((mx - tw // 2, my - 10), label, font=f, fill=color)


BG = (247, 246, 243)
INK = (22, 24, 29)
MUTE = (92, 100, 112)
COPPER = (179, 92, 46)
STEEL = (47, 95, 138)
WHITE = (255, 255, 255)
LINE = (228, 225, 218)
SOFT = (255, 250, 246)


def diagram_architecture():
    w, h = 1400, 900
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)
    title_f = font(36, True)
    sub_f = font(20)
    box_f = font(22, True)
    small_f = font(18)
    tiny_f = font(16)

    d.text((48, 36), "Aegis Architecture", font=title_f, fill=INK)
    d.text(
        (48, 86),
        "From live traffic to structured root-cause reports",
        font=sub_f,
        fill=MUTE,
    )

    boxes = [
        (100, 160, 280, 120, "Engineer / Agent", ["UI  ·  REST  ·  MCP clients"], STEEL),
        (
            520,
            160,
            360,
            160,
            "Aegis",
            ["FastAPI desk + API", "Aegis MCP (/mcp)", "Investigation services"],
            COPPER,
        ),
        (
            100,
            420,
            320,
            140,
            "OpenTelemetry",
            ["Traces · Logs · Metrics", "OTLP HTTP + ingestion key"],
            STEEL,
        ),
        (
            520,
            400,
            360,
            180,
            "SigNoz Cloud",
            ["Store & explore signals", "SigNoz MCP evidence", "Dashboards & alerts"],
            STEEL,
        ),
        (
            980,
            420,
            320,
            160,
            "RCA Report",
            ["Severity · Timeline", "Playbook · Export", "Deep links to SigNoz"],
            COPPER,
        ),
    ]

    for x, y, bw, bh, title, lines, accent in boxes:
        rounded_rect(d, (x, y, x + bw, y + bh), 18, WHITE, LINE, 2)
        d.rectangle((x, y, x + 10, y + bh), fill=accent)
        d.text((x + 28, y + 18), title, font=box_f, fill=INK)
        for i, line in enumerate(lines):
            d.text((x + 28, y + 58 + i * 28), line, font=small_f, fill=MUTE)

    arrow(d, 380, 220, 520, 220, "HTTP / MCP", tiny_f)
    arrow(d, 700, 320, 700, 400, "OTLP", tiny_f)
    arrow(d, 420, 490, 520, 490, "SigNoz MCP", tiny_f)
    arrow(d, 880, 490, 980, 490, "RCA", tiny_f)

    d.text(
        (48, 820),
        "Evidence path prefers SigNoz MCP. REST query is fallback only.",
        font=tiny_f,
        fill=MUTE,
    )
    img.save(out / "01-architecture.png", "PNG")
    print("wrote 01-architecture.png")


def diagram_pipeline():
    w, h = 1400, 700
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)
    title_f = font(36, True)
    sub_f = font(20)
    box_f = font(20, True)
    small_f = font(17)
    tiny_f = font(16)

    d.text((48, 36), "Investigation Pipeline", font=title_f, fill=INK)
    d.text((48, 86), "What happens when you click Run probe", font=sub_f, fill=MUTE)

    steps = [
        ("1", "Inject / Traffic", "Faults, orders,\nlive requests"),
        ("2", "Export OTEL", "Spans, logs,\nmetrics to Cloud"),
        ("3", "Collect Evidence", "SigNoz MCP:\ntraces · logs · alerts"),
        ("4", "Reason", "Online or offline\nstructured RCA"),
        ("5", "Enrich & Report", "Severity, timeline,\nplaybook, export"),
    ]
    bw, bh = 200, 200
    gap = 40
    start_x = 60
    y = 220
    for i, (num, title, body) in enumerate(steps):
        x = start_x + i * (bw + gap)
        rounded_rect(d, (x, y, x + bw, y + bh), 16, WHITE, LINE, 2)
        d.ellipse((x + bw // 2 - 22, y + 20, x + bw // 2 + 22, y + 64), fill=COPPER)
        center_text(
            d, (x + bw // 2 - 22, y + 20, x + bw // 2 + 22, y + 64), num, box_f, WHITE
        )
        d.text((x + 16, y + 84), title, font=box_f, fill=INK)
        for j, line in enumerate(body.split("\n")):
            d.text((x + 16, y + 124 + j * 26), line, font=small_f, fill=MUTE)
        if i < len(steps) - 1:
            ax1 = x + bw + 4
            ax2 = x + bw + gap - 4
            ay = y + bh // 2
            d.line((ax1, ay, ax2, ay), fill=COPPER, width=3)
            d.polygon([(ax2, ay), (ax2 - 10, ay - 6), (ax2 - 10, ay + 6)], fill=COPPER)

    d.text(
        (48, 520),
        "Empty evidence windows return an honest empty report — Aegis does not invent root causes.",
        font=tiny_f,
        fill=MUTE,
    )
    d.text((48, 560), "Service name in SigNoz: aegis", font=small_f, fill=STEEL)
    img.save(out / "02-pipeline.png", "PNG")
    print("wrote 02-pipeline.png")


def diagram_dual_mcp():
    w, h = 1400, 800
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)
    title_f = font(36, True)
    sub_f = font(20)
    box_f = font(22, True)
    small_f = font(18)

    d.text((48, 36), "Dual MCP Design", font=title_f, fill=INK)
    d.text(
        (48, 86),
        "SigNoz MCP for evidence  ·  Aegis MCP for investigation actions",
        font=sub_f,
        fill=MUTE,
    )

    rounded_rect(d, (520, 180, 880, 300), 18, WHITE, COPPER, 3)
    center_text(d, (520, 180, 880, 240), "Agent / IDE / Human", box_f, INK)
    center_text(d, (520, 240, 880, 300), "UI  ·  REST  ·  MCP clients", small_f, MUTE)

    rounded_rect(d, (80, 400, 520, 680), 18, WHITE, LINE, 2)
    d.rectangle((80, 400, 90, 680), fill=STEEL)
    d.text((110, 420), "SigNoz MCP", font=box_f, fill=INK)
    d.text((110, 460), "Hosted by SigNoz Cloud", font=small_f, fill=MUTE)
    for i, t in enumerate(
        [
            "search traces / logs",
            "list alerts & services",
            "trace details",
            "observability queries",
        ]
    ):
        d.text((110, 510 + i * 36), "•  " + t, font=small_f, fill=INK)

    rounded_rect(d, (880, 400, 1320, 680), 18, SOFT, COPPER, 2)
    d.rectangle((880, 400, 890, 680), fill=COPPER)
    d.text((910, 420), "Aegis MCP", font=box_f, fill=INK)
    d.text((910, 460), "Runs inside Aegis (/mcp)", font=small_f, fill=MUTE)
    for i, t in enumerate(
        [
            "aegis_investigate",
            "aegis_evidence",
            "aegis_fault",
            "aegis_history / links",
        ]
    ):
        d.text((910, 510 + i * 36), "•  " + t, font=small_f, fill=INK)

    arrow(d, 620, 300, 300, 400, "read", font(16))
    arrow(d, 780, 300, 1100, 400, "act", font(16))

    d.text(
        (48, 720),
        "One investigation backend. Two MCP surfaces. Humans and agents get the same truth.",
        font=small_f,
        fill=MUTE,
    )
    img.save(out / "03-dual-mcp.png", "PNG")
    print("wrote 03-dual-mcp.png")


def diagram_before_after():
    w, h = 1400, 720
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)
    title_f = font(36, True)
    box_f = font(24, True)
    small_f = font(18)

    d.text((48, 36), "Before and After Aegis", font=title_f, fill=INK)

    rounded_rect(d, (60, 140, 640, 640), 18, WHITE, LINE, 2)
    d.text((90, 170), "Before", font=box_f, fill=MUTE)
    for i, t in enumerate(
        [
            "Alert fires",
            "Open traces manually",
            "Search logs separately",
            "Compare timestamps",
            "Guess root cause",
            "Write notes by hand",
        ]
    ):
        y = 240 + i * 55
        d.ellipse((90, y + 6, 110, y + 26), outline=MUTE, width=2)
        if i < 5:
            d.line((100, y + 26, 100, y + 55), fill=LINE, width=2)
        d.text((130, y), t, font=small_f, fill=INK)

    rounded_rect(d, (760, 140, 1340, 640), 18, SOFT, COPPER, 2)
    d.text((790, 170), "With Aegis", font=box_f, fill=COPPER)
    for i, t in enumerate(
        [
            "Inject fault or real traffic",
            "OTLP lands in SigNoz Cloud",
            "One probe collects evidence",
            "Reasoner writes structured RCA",
            "Severity + timeline + playbook",
            "Export or open SigNoz traces",
        ]
    ):
        y = 240 + i * 55
        d.ellipse((790, y + 6, 810, y + 26), fill=COPPER)
        if i < 5:
            d.line((800, y + 26, 800, y + 55), fill=COPPER, width=2)
        d.text((830, y), t, font=small_f, fill=INK)

    img.save(out / "04-before-after.png", "PNG")
    print("wrote 04-before-after.png")


if __name__ == "__main__":
    diagram_architecture()
    diagram_pipeline()
    diagram_dual_mcp()
    diagram_before_after()
    print("done")
