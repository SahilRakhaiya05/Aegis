/* Aegis desk — white UI, dual MCP, severity + timeline + export */
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];

const state = { lastReport: null, health: null };

const TITLES = {
  home: ["Home", "Incident desk"],
  probe: ["Probe", "Evidence & workload"],
  faults: ["Faults", "Inject live failures"],
  mcp: ["MCP", "SigNoz MCP + Aegis MCP"],
  wire: ["SigNoz", "Instance links & queries"],
};

function esc(s) {
  return String(s ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function toast(msg) {
  const el = $("#toast");
  el.hidden = false;
  el.textContent = msg;
  clearTimeout(toast._t);
  toast._t = setTimeout(() => { el.hidden = true; }, 2800);
}

function setFoot(msg) { $("#foot-right").textContent = msg; }

async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
    ...opts,
  });
  const text = await res.text();
  let data;
  try { data = text ? JSON.parse(text) : {}; } catch { data = { raw: text }; }
  if (!res.ok) {
    const detail = data.detail || data.error || data.summary || res.statusText;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

function setPanel(name) {
  $$(".nav-btn").forEach((b) => b.classList.toggle("is-active", b.dataset.panel === name));
  $$(".panel").forEach((p) => {
    const on = p.id === `panel-${name}`;
    p.classList.toggle("is-active", on);
    p.hidden = !on;
  });
  const [title, eye] = TITLES[name] || ["Aegis", ""];
  $("#title").textContent = title;
  $("#eyebrow").textContent = eye;
}

function metric(label, value, cls = "", bar = null) {
  const barHtml = bar != null
    ? `<div class="bar"><i style="width:${Math.max(0, Math.min(100, bar))}%"></i></div>`
    : "";
  return `<div class="metric ${cls}"><div class="k">${esc(label)}</div><div class="v">${esc(value)}</div>${barHtml}</div>`;
}

function mini(label, value) {
  return `<div class="mini"><div class="k">${label}</div><div class="v">${esc(value)}</div></div>`;
}

function payload() {
  return {
    service: $("#service").value.trim() || "aegis",
    lookback_minutes: Number($("#lookback").value || 30),
    include_alerts: $("#include-alerts").checked,
    include_services: $("#include-services").checked,
  };
}

function reasonerLabel(r) {
  if (!r) return "—";
  if (typeof r === "string") {
    return ["mock", "offline"].includes(r) ? "offline" : "online";
  }
  if (r.status) return r.status === "offline" ? "offline" : "online";
  return "online";
}

function setPipeline(active, done = []) {
  const pipe = $("#pipeline");
  if (!active && !done.length) {
    pipe.hidden = true;
    return;
  }
  pipe.hidden = false;
  $$(".pipe-step").forEach((el) => {
    const step = el.dataset.step;
    el.classList.remove("on", "done");
    if (done.includes(step)) el.classList.add("done");
    if (step === active) el.classList.add("on");
  });
}

function renderTimeline(events) {
  const el = $("#timeline");
  const count = $("#tl-count");
  if (!events?.length) {
    el.className = "timeline empty";
    el.textContent = "Timeline fills after a probe.";
    count.textContent = "0 events";
    return;
  }
  count.textContent = `${events.length} events`;
  el.className = "timeline";
  el.innerHTML = events.map((e) => `
    <div class="tl-item">
      <div class="tl-kind ${esc(e.kind || "")}">${esc(e.kind || "event")}</div>
      <div>
        <div class="tl-title">${esc(e.title || "—")}</div>
        <div class="tl-detail">${esc(e.detail || "")}</div>
      </div>
    </div>
  `).join("");
}

function renderPlaybook(steps) {
  const el = $("#playbook");
  if (!steps?.length) {
    el.className = "playbook empty";
    el.innerHTML = "<li>Run a probe to generate next steps.</li>";
    return;
  }
  el.className = "playbook";
  el.innerHTML = steps.map((s) => `<li>${esc(s)}</li>`).join("");
}

function renderReport(r) {
  const box = $("#report");
  const pill = $("#report-pill");
  const sevEl = $("#report-sev");
  const actions = $("#report-actions");
  state.lastReport = r || null;

  if (!r || !r.summary) {
    box.className = "report empty";
    box.textContent = "No report yet. Inject a fault, wait for ingest, then run a probe.";
    pill.textContent = "idle";
    pill.className = "pill";
    sevEl.hidden = true;
    actions.hidden = true;
    renderTimeline([]);
    renderPlaybook([]);
    return;
  }

  const sev = r.severity || {};
  pill.textContent = r.evidence_source || r.confidence || "done";
  pill.className = `pill ${r.confidence === "low" ? "warn" : "ok"}`;
  if (sev.label) {
    sevEl.hidden = false;
    sevEl.className = `sev ${sev.label}`;
    sevEl.textContent = `${sev.label} · ${sev.score ?? "—"}`;
  } else {
    sevEl.hidden = true;
  }
  actions.hidden = false;
  if (r.investigation_id) {
    $("#btn-export-json").href = `/api/v1/investigate/history/${r.investigation_id}/export.json`;
    $("#btn-export-md").onclick = () => {
      window.open(`/api/v1/investigate/history/${r.investigation_id}/export.md`, "_blank");
    };
  }
  const traces = r.signoz_links?.traces;
  if (traces) {
    $("#btn-open-traces").href = traces;
    $("#btn-open-traces").hidden = false;
  }

  if (r.signoz_queries) {
    $("#query-snips").textContent = JSON.stringify(r.signoz_queries, null, 2);
  }

  const rows = [
    ["Summary", r.summary],
    ["Affected service", r.affected_service],
    ["Root cause", r.root_cause],
    ["Impact", r.impact],
    ["Fix", r.suggested_resolution],
    ["Confidence", r.confidence],
    ["Evidence", r.evidence_source],
    ["Reasoner", reasonerLabel(r.llm_provider)],
    ["Counts", r.evidence_counts ? JSON.stringify(r.evidence_counts) : "—"],
    ["Trace IDs", (r.trace_ids || []).slice(0, 5).join(", ") || "—"],
    ["Duration", r.duration_ms != null ? `${r.duration_ms} ms` : "—"],
    ["ID", r.investigation_id],
  ];
  box.className = "report";
  box.innerHTML = rows
    .filter(([, v]) => v != null && v !== "")
    .map(([k, v]) => {
      const mono = ["ID", "Counts", "Evidence", "Reasoner", "Trace IDs", "Duration"].includes(k);
      return `<div class="block"><span class="lbl">${esc(k)}</span><div class="val${mono ? " mono" : ""}">${esc(String(v))}</div></div>`;
    })
    .join("");

  renderTimeline(r.timeline || []);
  renderPlaybook(r.playbook || []);
}

async function refreshStats() {
  try {
    const s = await api("/api/v1/investigate/stats");
    $("#rail-inv").textContent = `${s.investigations} probe${s.investigations === 1 ? "" : "s"}`;
    const b = s.severity_breakdown || {};
    $("#rail-sev").textContent = `crit ${b.critical || 0} · elev ${b.elevated || 0} · mod ${b.moderate || 0}`;
  } catch {
    /* ignore */
  }
}

async function refresh() {
  try {
    const deep = await api("/api/v1/health/deep");
    state.health = deep;
    const apiOk = !!deep.signoz?.api?.ok;
    const smcpOk = !!deep.mcp?.signoz?.ok || !!deep.signoz?.mcp?.ok;
    const smcpTools = deep.mcp?.signoz?.tool_count ?? deep.signoz?.mcp?.tool_count ?? "—";
    const pmcpTools = deep.mcp?.aegis?.tool_count ?? deep.mcp?.product?.tool_count ?? "—";
    const reasoner = reasonerLabel(deep.reasoner);

    $("#status-cards").innerHTML = [
      metric("Overall", deep.status, deep.status === "healthy" ? "ok" : "warn"),
      metric("SigNoz API", apiOk ? "up" : "down", apiOk ? "ok" : "bad"),
      metric("SigNoz MCP", smcpOk ? `${smcpTools} tools` : "down", smcpOk ? "ok" : "bad"),
      metric("Aegis MCP", `${pmcpTools} tools`, "ok"),
    ].join("");

    $("#home-stats").innerHTML = [
      mini("Service", deep.service || "aegis"),
      mini("Version", deep.version || "1.0.0"),
      mini("Reasoner", reasoner),
      mini("OTEL", deep.otel?.protocol || "http"),
    ].join("");

    const url = deep.signoz?.url || "";
    const ia = $("#instance-a");
    ia.href = url || "#";
    ia.textContent = url || "—";

    const dot = $("#live-dot");
    if (apiOk || smcpOk) {
      dot.className = "live-dot ok";
      dot.innerHTML = "<i></i><span>live</span>";
    } else {
      dot.className = "live-dot bad";
      dot.innerHTML = "<i></i><span>degraded</span>";
    }

    $("#smcp-url").textContent = deep.mcp?.signoz?.url || deep.signoz?.mcp_url || "—";
    $("#smcp-open").href = deep.mcp?.signoz?.url || deep.signoz?.mcp_url || "#";
    $("#smcp-pill").textContent = smcpOk ? "connected" : "down";
    $("#smcp-pill").className = `pill ${smcpOk ? "ok" : "bad"}`;
    $("#pmcp-pill").textContent = "ready";
    $("#pmcp-pill").className = "pill ok";

    const L = deep.signoz?.links || {};
    $("#wire-kv").innerHTML = [
      kv("Instance", url ? `<a href="${esc(url)}" target="_blank" rel="noreferrer">${esc(url)}</a>` : "—"),
      kv("Service", esc(L.service_name || deep.service || "aegis")),
      kv("SigNoz MCP", esc(deep.mcp?.signoz?.url || "")),
      kv("Aegis MCP", "/mcp"),
      kv("OTLP", esc(deep.otel?.endpoint || "")),
      kv("Protocol", esc(deep.otel?.protocol || "")),
      kv("Headers", deep.otel?.headers_configured ? "set" : "missing"),
      kv("API", apiOk ? "ok" : "fail"),
      kv("SigNoz MCP", smcpOk ? `ok · ${smcpTools}` : "fail"),
      kv("Aegis MCP", `ok · ${pmcpTools}`),
    ].join("");

    const a = (label, href) =>
      href ? `<a href="${esc(href)}" target="_blank" rel="noreferrer">${esc(label)}</a>` : "";
    $("#wire-links").innerHTML = [
      a("Services", L.services),
      a("Traces", L.traces),
      a("Logs", L.logs),
      a("Metrics", L.metrics),
      a("Dashboards", L.dashboards),
      a("Alerts", L.alerts),
      a("Ingestion", L.ingestion_settings),
      a("Aegis MCP", "/mcp"),
    ].join("");

    $("#foot-left").textContent = `${deep.product || "Aegis"} ${deep.version || ""}`.trim();
    $("#foot-mid").textContent = deep.service || "aegis";
    setFoot(`reasoner ${reasoner}`);
    await refreshStats();
  } catch (err) {
    $("#status-cards").innerHTML = metric("Health", err.message, "bad");
    $("#live-dot").className = "live-dot bad";
    $("#live-dot").innerHTML = "<i></i><span>offline</span>";
    setFoot(err.message);
  }
}

function kv(k, vHtml) {
  return `<div><dt>${esc(k)}</dt><dd>${vHtml}</dd></div>`;
}

async function loadHistory() {
  try {
    const data = await api("/api/v1/investigate/history?limit=16");
    const items = data.items || [];
    if (!items.length) {
      $("#history").textContent = "Nothing this session.";
      return;
    }
    $("#history").innerHTML = items.map((it) => {
      const sev = it.severity?.label || "";
      return `
      <button type="button" class="item" data-id="${esc(it.investigation_id)}">
        <div class="t">${esc((it.created_at || "").slice(0, 19))} · ${esc(it.evidence_source || "")}${sev ? ` · ${esc(sev)}` : ""}</div>
        <div class="s">${esc((it.summary || "").slice(0, 140))}</div>
      </button>`;
    }).join("");
    $$("#history .item").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const r = await api(`/api/v1/investigate/history/${btn.dataset.id}`);
        setPanel("home");
        renderReport(r);
        toast("Loaded report");
      });
    });
    await refreshStats();
  } catch (err) {
    $("#history").textContent = err.message;
  }
}

async function loadOrders() {
  try {
    const items = await api("/api/v1/workload/orders");
    if (!items.length) {
      $("#orders").textContent = "No orders yet.";
      return;
    }
    $("#orders").innerHTML = items.slice().reverse().map((o) => `
      <div class="item" style="cursor:default">
        <div class="t">${esc(o.id)}</div>
        <div class="s">${esc(o.item)} × ${esc(o.quantity)} · ${esc(o.status)}</div>
      </div>
    `).join("");
  } catch (err) {
    $("#orders").textContent = err.message;
  }
}

async function runProbe() {
  const btns = [$("#btn-run"), $("#home-form button[type=submit]")].filter(Boolean);
  btns.forEach((b) => { b.disabled = true; });
  setPanel("home");
  setPipeline("collect");
  $("#report-pill").textContent = "running";
  $("#report-pill").className = "pill warn";
  $("#report").className = "report";
  $("#report").innerHTML = `<div class="block"><span class="lbl">Status</span><div class="val">Collecting evidence via SigNoz MCP…</div></div>`;
  try {
    setTimeout(() => setPipeline("reason", ["collect"]), 400);
    const report = await api("/api/v1/investigate", {
      method: "POST",
      body: JSON.stringify(payload()),
    });
    setPipeline("report", ["collect", "reason"]);
    renderReport(report);
    await loadHistory();
    toast("Probe complete");
    setFoot(`evidence ${report.evidence_source || "—"} · ${report.severity?.label || ""}`);
    setTimeout(() => setPipeline(null), 1200);
  } catch (err) {
    $("#report").innerHTML = `<div class="block"><span class="lbl">Error</span><div class="val">${esc(err.message)}</div></div>`;
    $("#report-pill").textContent = "error";
    $("#report-pill").className = "pill bad";
    toast(err.message);
    setPipeline(null);
  } finally {
    btns.forEach((b) => { b.disabled = false; });
  }
}

async function fetchEvidence() {
  setPanel("probe");
  $("#evidence-out").textContent = "Fetching…";
  $("#ev-highlights").innerHTML = "";
  try {
    const data = await api("/api/v1/investigate/evidence", {
      method: "POST",
      body: JSON.stringify(payload()),
    });
    $("#evidence-out").textContent = JSON.stringify(data, null, 2);
    const chips = [];
    if (data.counts) {
      Object.entries(data.counts).forEach(([k, v]) => chips.push(`<span class="chip"><b>${esc(k)}</b>${esc(v)}</span>`));
    }
    if (data.highlights?.top_span) chips.push(`<span class="chip"><b>span</b>${esc(data.highlights.top_span)}</span>`);
    if (data.trace_ids?.length) chips.push(`<span class="chip"><b>traces</b>${esc(data.trace_ids.length)}</span>`);
    $("#ev-highlights").innerHTML = chips.join("");
    if (data.timeline) renderTimeline(data.timeline);
    toast("Evidence ready");
  } catch (err) {
    $("#evidence-out").textContent = err.message;
  }
}

async function fireFault(kind) {
  try {
    if (kind === "storm") {
      const data = await api("/api/v1/chaos/storm?count=8", { method: "POST" });
      $("#fault-out").textContent = JSON.stringify(data, null, 2);
      toast("Storm sent");
    } else {
      const res = await fetch(`/api/v1/chaos/${kind}`);
      const text = await res.text();
      $("#fault-out").textContent = `${res.status}\n${text}`;
      toast(`${kind} → ${res.status}`);
    }
  } catch (err) {
    $("#fault-out").textContent = err.message;
  }
}

async function runDemo() {
  const btn = $("#btn-demo");
  if (btn) { btn.disabled = true; btn.textContent = "Running…"; }
  setPipeline("collect");
  toast("Dry-run started");
  try {
    setTimeout(() => setPipeline("reason", ["collect"]), 800);
    const data = await api("/api/v1/demo/run?wait_seconds=12&lookback_minutes=30&storm_count=6", {
      method: "POST",
    });
    setPipeline("report", ["collect", "reason"]);
    setPanel("home");
    renderReport(data.report);
    await loadHistory();
    toast("Dry-run complete");
    setTimeout(() => setPipeline(null), 1200);
  } catch (err) {
    toast(err.message);
    setPipeline(null);
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = "Full dry-run"; }
  }
}

function renderToolList(el, tools) {
  if (!tools?.length) {
    el.textContent = "No tools.";
    return;
  }
  el.innerHTML = tools.map((t) => `
    <div class="item" style="cursor:default">
      <div class="t">${esc(t.name)}</div>
      <div class="s">${esc(t.description || "")}</div>
    </div>
  `).join("");
}

async function loadSignozMcp() {
  $("#smcp-tools").textContent = "Loading…";
  try {
    const data = await api("/api/v1/signoz/mcp/tools");
    if (!data.ok) {
      $("#smcp-tools").textContent = data.error || "Failed";
      return;
    }
    renderToolList($("#smcp-tools"), data.tools);
    toast(`SigNoz MCP · ${data.count} tools`);
  } catch (err) {
    $("#smcp-tools").textContent = err.message;
  }
}

async function loadProductMcp() {
  $("#pmcp-tools").textContent = "Loading…";
  try {
    const data = await api("/api/v1/mcp/tools");
    renderToolList($("#pmcp-tools"), data.tools);
    $("#pmcp-sample").textContent = JSON.stringify(
      {
        jsonrpc: "2.0",
        id: 1,
        method: "tools/call",
        params: {
          name: "aegis_investigate",
          arguments: { service: "aegis", lookback_minutes: 30 },
        },
      },
      null,
      2,
    );
    toast(`Aegis MCP · ${data.count} tools`);
  } catch (err) {
    $("#pmcp-tools").textContent = err.message;
  }
}

async function pingProductMcp() {
  toast("Calling aegis_investigate via MCP…");
  setPipeline("collect");
  try {
    const r = await api("/mcp", {
      method: "POST",
      body: JSON.stringify({
        jsonrpc: "2.0",
        id: 99,
        method: "tools/call",
        params: {
          name: "aegis_investigate",
          arguments: payload(),
        },
      }),
    });
    const text = r?.result?.content?.[0]?.text;
    if (text) {
      try {
        const report = JSON.parse(text);
        setPanel("home");
        setPipeline("report", ["collect", "reason"]);
        renderReport(report);
        await loadHistory();
        toast("MCP probe complete");
        setTimeout(() => setPipeline(null), 1000);
        return;
      } catch { /* fall through */ }
    }
    $("#pmcp-sample").textContent = JSON.stringify(r, null, 2);
    toast("MCP response received");
    setPipeline(null);
  } catch (err) {
    toast(err.message);
    setPipeline(null);
  }
}

/* Events */
$$(".nav-btn").forEach((b) => b.addEventListener("click", () => setPanel(b.dataset.panel)));
$$("[data-goto]").forEach((b) => b.addEventListener("click", () => setPanel(b.dataset.goto)));
$("#btn-refresh").addEventListener("click", async () => { await refresh(); toast("Refreshed"); });
$("#btn-run").addEventListener("click", runProbe);
$("#btn-hist").addEventListener("click", loadHistory);
$("#btn-demo").addEventListener("click", runDemo);
$("#btn-evidence").addEventListener("click", fetchEvidence);
$("#btn-evidence-2")?.addEventListener("click", fetchEvidence);
$("#btn-smcp").addEventListener("click", loadSignozMcp);
$("#btn-pmcp").addEventListener("click", loadProductMcp);
$("#btn-pmcp-ping")?.addEventListener("click", pingProductMcp);

$("#btn-copy")?.addEventListener("click", async () => {
  if (!state.lastReport) return;
  const text = JSON.stringify(state.lastReport, null, 2);
  try {
    await navigator.clipboard.writeText(text);
    toast("Report copied");
  } catch {
    toast("Copy failed");
  }
});

$("#home-form").addEventListener("submit", (e) => {
  e.preventDefault();
  runProbe();
});

document.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
    e.preventDefault();
    runProbe();
  }
});

$$("[data-fault]").forEach((b) => {
  b.addEventListener("click", () => fireFault(b.getAttribute("data-fault")));
});

$("#order-form")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    const body = {
      item: $("#order-item").value.trim() || "widget",
      quantity: Number($("#order-qty").value || 1),
    };
    const res = await fetch("/api/v1/workload/orders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const text = await res.text();
    let data;
    try { data = JSON.parse(text); } catch { data = { raw: text }; }
    $("#order-out").textContent = `${res.status}\n${JSON.stringify(data, null, 2)}`;
    toast(res.ok ? "Order placed" : "Order failed");
    await loadOrders();
  } catch (err) {
    $("#order-out").textContent = err.message;
  }
});

refresh();
loadHistory();
loadOrders();
setInterval(refresh, 45000);
