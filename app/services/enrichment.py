"""Enrich investigation reports with severity, timeline, and SigNoz deep links."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.domain.models import EvidenceBundle
from app.integrations.signoz import links as signoz_links


def severity_score(counts: Dict[str, Any], confidence: Optional[str]) -> Dict[str, Any]:
    traces = int(counts.get("error_traces") or 0)
    logs = int(counts.get("error_logs") or 0)
    alerts = int(counts.get("alerts") or 0)
    raw = min(100, traces * 18 + logs * 8 + alerts * 12)
    if confidence == "high":
        raw = min(100, raw + 10)
    elif confidence == "low":
        raw = max(0, raw - 8)

    if raw >= 70:
        label = "critical"
    elif raw >= 40:
        label = "elevated"
    elif raw >= 15:
        label = "moderate"
    else:
        label = "low"
    return {"score": raw, "label": label}


def extract_trace_ids(evidence: EvidenceBundle, limit: int = 8) -> List[str]:
    ids: List[str] = []
    for t in evidence.error_traces:
        if not isinstance(t, dict):
            continue
        tid = t.get("traceID") or t.get("traceId") or t.get("trace_id")
        if tid and str(tid) not in ids:
            ids.append(str(tid))
        if len(ids) >= limit:
            break
    return ids


def build_timeline(evidence: EvidenceBundle, limit: int = 12) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []

    for t in evidence.error_traces[:8]:
        if not isinstance(t, dict):
            continue
        events.append(
            {
                "kind": "trace",
                "title": t.get("name") or t.get("spanName") or "error span",
                "detail": t.get("statusMessage")
                or t.get("traceID")
                or t.get("traceId")
                or "",
                "ts": t.get("timestamp") or t.get("startTime") or "",
            }
        )

    for log in evidence.error_logs[:8]:
        if not isinstance(log, dict):
            continue
        body = (
            log.get("body")
            or log.get("message")
            or log.get("log")
            or str(log)[:160]
        )
        events.append(
            {
                "kind": "log",
                "title": str(log.get("severity_text") or log.get("severity") or "ERROR"),
                "detail": str(body)[:220],
                "ts": log.get("timestamp") or log.get("time") or "",
            }
        )

    for a in (evidence.alerts or [])[:4]:
        if isinstance(a, dict):
            events.append(
                {
                    "kind": "alert",
                    "title": a.get("name") or a.get("alertname") or "alert",
                    "detail": a.get("state") or a.get("status") or "",
                    "ts": a.get("startsAt") or a.get("timestamp") or "",
                }
            )
        else:
            events.append(
                {
                    "kind": "alert",
                    "title": "alert",
                    "detail": str(a)[:160],
                    "ts": "",
                }
            )

    return events[:limit]


def signoz_queries(service: str) -> Dict[str, str]:
    return {
        "error_traces": f"serviceName = '{service}' AND hasError = true",
        "error_logs": f"service.name = '{service}' AND severity_text IN ('ERROR','FATAL')",
        "service_filter": service,
    }


def playbook_steps(service: str, counts: Dict[str, Any]) -> List[str]:
    steps = [
        f"Open SigNoz traces for service `{service}` with hasError = true.",
        "Correlate ERROR logs to failing span/trace IDs.",
        "Confirm whether latency (p95) rose in the same window.",
        "Apply the suggested resolution and re-run a probe to verify.",
    ]
    if int(counts.get("alerts") or 0) > 0:
        steps.insert(2, "Review firing alerts collected during the probe.")
    if int(counts.get("error_traces") or 0) == 0:
        steps = [
            "Generate traffic or inject faults so error spans appear.",
            "Wait 15–30s for SigNoz Cloud ingestion.",
            "Re-run the probe with a wider lookback window.",
        ]
    return steps


def enrich_payload(evidence: EvidenceBundle, confidence: Optional[str]) -> Dict[str, Any]:
    service = evidence.service
    counts = evidence.counts or {}
    return {
        "severity": severity_score(counts, confidence),
        "timeline": build_timeline(evidence),
        "trace_ids": extract_trace_ids(evidence),
        "signoz_queries": signoz_queries(service),
        "signoz_links": signoz_links.all_links(service),
        "playbook": playbook_steps(service, counts),
        "highlights": {
            "top_span": (
                (evidence.error_traces[0].get("name") if evidence.error_traces and isinstance(evidence.error_traces[0], dict) else None)
            ),
            "top_log": (
                str(
                    (evidence.error_logs[0].get("body") if evidence.error_logs and isinstance(evidence.error_logs[0], dict) else "")
                    or (evidence.error_logs[0].get("message") if evidence.error_logs and isinstance(evidence.error_logs[0], dict) else "")
                )[:180]
                if evidence.error_logs
                else None
            ),
        },
    }


def report_to_markdown(report: Dict[str, Any]) -> str:
    sev = (report.get("severity") or {})
    lines = [
        f"# Aegis investigation {report.get('investigation_id', '')}",
        "",
        f"- **Service:** {report.get('affected_service')}",
        f"- **Confidence:** {report.get('confidence')}",
        f"- **Severity:** {sev.get('label')} ({sev.get('score')})",
        f"- **Evidence:** {report.get('evidence_source')}",
        f"- **Created:** {report.get('created_at')}",
        "",
        "## Summary",
        report.get("summary") or "—",
        "",
        "## Root cause",
        report.get("root_cause") or "—",
        "",
        "## Impact",
        report.get("impact") or "—",
        "",
        "## Suggested resolution",
        report.get("suggested_resolution") or "—",
        "",
        "## Evidence counts",
        f"`{report.get('evidence_counts')}`",
        "",
    ]
    pb = report.get("playbook") or []
    if pb:
        lines.append("## Playbook")
        for i, step in enumerate(pb, 1):
            lines.append(f"{i}. {step}")
        lines.append("")
    return "\n".join(lines)
