"""Collect incident evidence from SigNoz MCP + Query API."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

from app.domain.models import EvidenceBundle
from app.integrations.signoz.mcp import SignozMCPClient
from app.integrations.signoz.query_api import query_client
from app.settings import settings

logger = logging.getLogger(__name__)


async def collect_evidence(
    service: str,
    start_ms: int,
    end_ms: int,
    *,
    include_alerts: bool = True,
    include_services: bool = False,
) -> EvidenceBundle:
    traces: List[dict] = []
    logs: List[dict] = []
    latency: List[dict] = []
    alerts: List[Any] = []
    services: List[Any] = []
    notes: List[str] = []
    source = "empty"

    use_mcp = bool(settings.SIGNOZ_USE_MCP and settings.SIGNOZ_MCP_URL)
    if use_mcp:
        try:
            traces, logs, alerts, services, mcp_notes = await _via_mcp(
                service,
                start_ms,
                end_ms,
                include_alerts=include_alerts,
                include_services=include_services,
            )
            notes.extend(mcp_notes)
            source = "signoz_mcp"
        except Exception as exc:
            logger.warning("MCP evidence failed, API fallback: %s", exc)
            notes.append(f"mcp_fallback: {exc}")
            use_mcp = False

    # REST Query API only when MCP is off or returned no core evidence.
    # Some Cloud keys authorize MCP + /version but not /api/v5/query_range.
    need_api = (not use_mcp) or (not traces and not logs)
    if need_api:
        api_traces, api_logs, api_latency, api_notes = await _via_api(
            service, start_ms, end_ms
        )
        notes.extend(api_notes)
        if not traces:
            traces = api_traces
        if not logs:
            logs = api_logs
        if not latency:
            latency = api_latency
        if source == "signoz_mcp" and (api_traces or api_logs or api_latency):
            source = "hybrid"
        elif source == "empty":
            source = "signoz_api"

    traces = traces[: settings.EVIDENCE_TRACE_LIMIT]
    logs = logs[: settings.EVIDENCE_LOG_LIMIT]
    latency = latency[:100]
    counts = {
        "error_traces": len(traces),
        "error_logs": len(logs),
        "latency_points": len(latency),
        "alerts": len(alerts),
        "services": len(services),
    }
    logger.info("Evidence collected source=%s counts=%s", source, counts)
    return EvidenceBundle(
        service=service,
        window={"start_ms": start_ms, "end_ms": end_ms},
        evidence_source=source,
        error_traces=traces,
        error_logs=logs,
        p95_latency_series=latency,
        alerts=alerts[:20],
        services=services[:50],
        notes=notes,
        counts=counts,
    )


async def _via_mcp(
    service: str,
    start_ms: int,
    end_ms: int,
    *,
    include_alerts: bool,
    include_services: bool,
) -> Tuple[List[dict], List[dict], List[Any], List[Any], List[str]]:
    notes: List[str] = []
    traces: List[dict] = []
    logs: List[dict] = []
    alerts: List[Any] = []
    services: List[Any] = []
    client = SignozMCPClient()
    await client.initialize()

    try:
        raw = await client.search_traces(
            service, start_ms, end_ms, errors_only=True, limit=settings.EVIDENCE_TRACE_LIMIT
        )
        traces = query_client.as_dict_list(raw)
        notes.append(f"mcp_traces={len(traces)}")
    except Exception as exc:
        notes.append(f"mcp_traces_failed: {exc}")

    try:
        raw = await client.search_logs(
            service, start_ms, end_ms, limit=settings.EVIDENCE_LOG_LIMIT
        )
        logs = query_client.as_dict_list(raw)
        notes.append(f"mcp_logs={len(logs)}")
    except Exception as exc:
        notes.append(f"mcp_logs_failed: {exc}")

    if include_alerts:
        try:
            raw = await client.list_alerts()
            if isinstance(raw, list):
                alerts = raw[:20]
            elif raw:
                alerts = [raw]
            notes.append(f"mcp_alerts={len(alerts)}")
        except Exception as exc:
            notes.append(f"mcp_alerts_failed: {exc}")

    if include_services:
        try:
            raw = await client.list_services(start_ms, end_ms)
            if isinstance(raw, list):
                services = raw[:50]
            elif raw:
                services = query_client.as_dict_list(raw)
            notes.append(f"mcp_services={len(services)}")
        except Exception as exc:
            notes.append(f"mcp_services_failed: {exc}")

    if traces:
        tid = (
            traces[0].get("traceID")
            or traces[0].get("traceId")
            or traces[0].get("trace_id")
        )
        if tid:
            try:
                details = await client.get_trace_details(str(tid))
                if details:
                    traces[0] = {
                        **traces[0],
                        "details": details
                        if isinstance(details, dict)
                        else {"raw": details},
                    }
                    notes.append("mcp_trace_details=ok")
            except Exception as exc:
                notes.append(f"mcp_trace_details_failed: {exc}")

    return traces, logs, alerts, services, notes


async def _via_api(
    service: str, start_ms: int, end_ms: int
) -> Tuple[List[dict], List[dict], List[dict], List[str]]:
    notes: List[str] = []
    traces: List[dict] = []
    logs: List[dict] = []
    latency: List[dict] = []
    try:
        traces = await query_client.error_traces(
            service, start_ms, end_ms, settings.EVIDENCE_TRACE_LIMIT
        )
        notes.append(f"api_traces={len(traces)}")
    except Exception as exc:
        logger.exception("API traces failed")
        notes.append(f"api_traces_failed: {exc}")
    try:
        logs = await query_client.error_logs(
            service, start_ms, end_ms, settings.EVIDENCE_LOG_LIMIT
        )
        notes.append(f"api_logs={len(logs)}")
    except Exception as exc:
        logger.exception("API logs failed")
        notes.append(f"api_logs_failed: {exc}")
    try:
        latency = await query_client.latency_p95(service, start_ms, end_ms)
        notes.append(f"api_latency={len(latency)}")
    except Exception as exc:
        logger.exception("API latency failed")
        notes.append(f"api_latency_failed: {exc}")
    return traces, logs, latency, notes
