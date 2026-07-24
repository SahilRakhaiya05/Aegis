"""Aegis investigation orchestrator."""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Optional

from app.domain.models import InvestigationReport, InvestigationRequest
from app.integrations.llm.router import complete, resolve_backend
from app.observability.instruments import investigations_total
from app.prompts.rca import ROOT_CAUSE_PROMPT, SYSTEM_PROMPT
from app.services import history
from app.services.enrichment import enrich_payload, report_to_markdown
from app.services.evidence import collect_evidence
from app.settings import settings

logger = logging.getLogger(__name__)


def _strip_fences(raw: str) -> str:
    cleaned = (raw or "").strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    if cleaned and not cleaned.startswith("{"):
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if match:
            cleaned = match.group(0)
    return cleaned


def resolve_window(req: InvestigationRequest) -> tuple[int, int]:
    end_ms = req.end_ms or int(time.time() * 1000)
    start_ms = req.start_ms or (end_ms - req.lookback_minutes * 60 * 1000)
    return start_ms, end_ms


def _finalize(
    report: InvestigationReport,
    evidence,
    confidence: Optional[str],
    started: float,
) -> InvestigationReport:
    extra = enrich_payload(evidence, confidence or report.confidence)
    report.severity = extra["severity"]
    report.timeline = extra["timeline"]
    report.trace_ids = extra["trace_ids"]
    report.signoz_queries = extra["signoz_queries"]
    report.signoz_links = extra["signoz_links"]
    report.playbook = extra["playbook"]
    report.highlights = extra["highlights"]
    report.duration_ms = round((time.perf_counter() - started) * 1000, 1)
    history.push(report)
    return report


async def investigate(req: InvestigationRequest) -> InvestigationReport:
    started = time.perf_counter()
    service = (req.service or settings.OTEL_SERVICE_NAME).strip()
    start_ms, end_ms = resolve_window(req)
    investigations_total.add(1, {"service": service})

    evidence = await collect_evidence(
        service,
        start_ms,
        end_ms,
        include_alerts=req.include_alerts,
        include_services=req.include_services,
    )
    counts = evidence.counts

    if counts.get("error_traces", 0) == 0 and counts.get("error_logs", 0) == 0:
        report = InvestigationReport(
            summary=(
                "No error traces or error logs found for this service in the given "
                "window. Inject faults, wait 15–30s for SigNoz ingestion, then probe again."
            ),
            affected_service=service,
            evidence_source=evidence.evidence_source,
            llm_provider=resolve_backend(),
            evidence_counts=counts,
            window=evidence.window,
            notes=evidence.notes,
            confidence="low",
        )
        return _finalize(report, evidence, "low", started)

    prompt = (
        f"{ROOT_CAUSE_PROMPT}\n\n"
        f"Evidence:\n{json.dumps(evidence.model_dump(), default=str, indent=2)}\n\n"
        "Return ONLY a valid JSON object."
    )
    try:
        llm = await complete(prompt, system=SYSTEM_PROMPT)
    except Exception:
        logger.exception("Reasoner failed")
        report = InvestigationReport(
            summary="Investigation failed: reasoner error.",
            affected_service=service,
            evidence_source=evidence.evidence_source,
            evidence_counts=counts,
            window=evidence.window,
            notes=evidence.notes,
            confidence="low",
        )
        return _finalize(report, evidence, "low", started)

    try:
        parsed = json.loads(_strip_fences(llm.text))
        if not isinstance(parsed, dict):
            raise TypeError("not an object")
    except (json.JSONDecodeError, TypeError):
        logger.error("Invalid reasoner JSON: %r", llm.text)
        report = InvestigationReport(
            summary="Analysis failed: reasoner did not return valid JSON.",
            affected_service=service,
            evidence_source=evidence.evidence_source,
            llm_provider=llm.provider,
            llm_model=llm.model,
            evidence_counts=counts,
            window=evidence.window,
            notes=evidence.notes,
            confidence="low",
        )
        return _finalize(report, evidence, "low", started)

    conf = parsed.get("confidence")
    report = InvestigationReport(
        summary=parsed.get("summary"),
        affected_service=parsed.get("affected_service") or service,
        root_cause=parsed.get("root_cause"),
        impact=parsed.get("impact"),
        suggested_resolution=parsed.get("suggested_resolution"),
        confidence=conf,
        evidence_source=evidence.evidence_source,
        llm_provider=llm.provider,
        llm_model=llm.model,
        evidence_counts=counts,
        window=evidence.window,
        notes=evidence.notes,
    )
    return _finalize(report, evidence, conf, started)


async def get_history(limit: int = 20):
    return history.list_reports(limit)


async def get_report(investigation_id: str) -> Optional[InvestigationReport]:
    return history.get(investigation_id)


async def export_markdown(investigation_id: str) -> Optional[str]:
    report = history.get(investigation_id)
    if not report:
        return None
    return report_to_markdown(report.model_dump())


def session_stats() -> dict:
    items = history.list_reports(100)
    sev_counts = {"critical": 0, "elevated": 0, "moderate": 0, "low": 0, "unknown": 0}
    for it in items:
        label = (it.severity or {}).get("label") if it.severity else None
        if label in sev_counts:
            sev_counts[label] += 1
        else:
            sev_counts["unknown"] += 1
    return {
        "investigations": len(items),
        "severity_breakdown": sev_counts,
        "latest_id": items[0].investigation_id if items else None,
        "service": settings.OTEL_SERVICE_NAME,
    }
