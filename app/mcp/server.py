"""
Aegis MCP (Model Context Protocol) — HTTP JSON-RPC.

Exposes investigation tools so agents/IDEs can call Aegis the same way
they call SigNoz MCP. Endpoint: POST /mcp
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List, Optional

from app.domain.models import InvestigationRequest
from app.integrations.signoz import links as signoz_links
from app.services import chaos as chaos_service
from app.services import investigation as inv
from app.services.evidence import collect_evidence
from app.services.investigation import resolve_window
from app.settings import settings

logger = logging.getLogger(__name__)

PROTOCOL_VERSION = "2024-11-05"

TOOLS: List[Dict[str, Any]] = [
    {
        "name": "aegis_health",
        "description": "Return Aegis health, SigNoz connectivity flags, and Aegis MCP info.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "aegis_investigate",
        "description": (
            "Run a full incident investigation for a service: collect SigNoz evidence "
            "and produce a structured root-cause report."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "service": {
                    "type": "string",
                    "description": "Service name (default: Aegis)",
                },
                "lookback_minutes": {
                    "type": "integer",
                    "description": "Lookback window in minutes",
                    "default": 30,
                },
                "include_alerts": {"type": "boolean", "default": True},
                "include_services": {"type": "boolean", "default": False},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "aegis_evidence",
        "description": "Collect SigNoz evidence only (traces/logs/alerts) without writing a report.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "service": {"type": "string"},
                "lookback_minutes": {"type": "integer", "default": 30},
                "include_alerts": {"type": "boolean", "default": True},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "aegis_history",
        "description": "List recent investigation reports from this Aegis process.",
        "inputSchema": {
            "type": "object",
            "properties": {"limit": {"type": "integer", "default": 10}},
            "additionalProperties": False,
        },
    },
    {
        "name": "aegis_fault",
        "description": "Inject a demo fault: error | latency | flaky | storm.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kind": {
                    "type": "string",
                    "enum": ["error", "latency", "flaky", "storm"],
                },
                "count": {
                    "type": "integer",
                    "description": "Storm size (storm only)",
                    "default": 8,
                },
            },
            "required": ["kind"],
            "additionalProperties": False,
        },
    },
    {
        "name": "aegis_signoz_links",
        "description": "Return deep links into the configured SigNoz Cloud instance.",
        "inputSchema": {
            "type": "object",
            "properties": {"service": {"type": "string"}},
            "additionalProperties": False,
        },
    },
]


def aegis_mcp_info() -> Dict[str, Any]:
    return {
        "name": "AegisMCP",
        "version": settings.SERVICE_VERSION,
        "url": "/mcp",
        "protocol": PROTOCOL_VERSION,
        "tool_count": len(TOOLS),
        "tools": [t["name"] for t in TOOLS],
        "transport": "http json-rpc",
        "signoz_mcp_url": settings.SIGNOZ_MCP_URL,
    }


def _text_result(payload: Any, *, is_error: bool = False) -> dict:
    if isinstance(payload, (dict, list)):
        text = json.dumps(payload, default=str, indent=2)
    else:
        text = str(payload)
    return {
        "content": [{"type": "text", "text": text}],
        "isError": is_error,
    }


async def _call_tool(name: str, arguments: Optional[dict]) -> dict:
    args = arguments or {}
    try:
        if name == "aegis_health":
            from app.integrations.llm.router import resolve_backend
            from app.integrations.signoz.mcp import mcp_health
            from app.integrations.signoz.query_api import query_client

            api = await query_client.ping()
            smcp = await mcp_health() if settings.SIGNOZ_USE_MCP else {"ok": False}
            return _text_result(
                {
                    "product": settings.PRODUCT_TITLE,
                    "service": settings.OTEL_SERVICE_NAME,
                    "signoz_api": api,
                    "signoz_mcp": smcp,
                    "aegis_mcp": aegis_mcp_info(),
                    "reasoner": resolve_backend(),
                }
            )

        if name == "aegis_investigate":
            req = InvestigationRequest(
                service=args.get("service") or settings.OTEL_SERVICE_NAME,
                lookback_minutes=int(args.get("lookback_minutes") or 30),
                include_alerts=bool(args.get("include_alerts", True)),
                include_services=bool(args.get("include_services", False)),
            )
            report = await inv.investigate(req)
            return _text_result(report.model_dump())

        if name == "aegis_evidence":
            req = InvestigationRequest(
                service=args.get("service") or settings.OTEL_SERVICE_NAME,
                lookback_minutes=int(args.get("lookback_minutes") or 30),
                include_alerts=bool(args.get("include_alerts", True)),
            )
            start_ms, end_ms = resolve_window(req)
            bundle = await collect_evidence(
                req.service or settings.OTEL_SERVICE_NAME,
                start_ms,
                end_ms,
                include_alerts=req.include_alerts,
            )
            return _text_result(bundle.model_dump())

        if name == "aegis_history":
            limit = int(args.get("limit") or 10)
            items = await inv.get_history(limit)
            return _text_result([i.model_dump() for i in items])

        if name == "aegis_fault":
            kind = str(args.get("kind") or "error")
            if kind == "error":
                # Don't raise HTTPException into MCP — log-level fault via storm-like error log
                logger.error("MCP fault inject: simulated downstream failure")
                return _text_result(
                    {"scenario": "error", "status": "injected", "detail": "ERROR logged"}
                )
            if kind == "latency":
                result = await chaos_service.simulate_latency()
                return _text_result(result.model_dump())
            if kind == "flaky":
                try:
                    result = await chaos_service.simulate_flaky()
                    return _text_result(result.model_dump())
                except Exception as exc:
                    return _text_result(
                        {"scenario": "flaky", "status": "failed", "detail": str(exc)}
                    )
            if kind == "storm":
                count = int(args.get("count") or 8)
                result = await chaos_service.simulate_storm(count)
                return _text_result(result.model_dump())
            return _text_result({"error": f"unknown kind {kind}"}, is_error=True)

        if name == "aegis_signoz_links":
            return _text_result(signoz_links.all_links(args.get("service")))

        return _text_result({"error": f"Unknown tool: {name}"}, is_error=True)
    except Exception as exc:
        logger.exception("MCP tool %s failed", name)
        return _text_result({"error": str(exc)}, is_error=True)


async def handle_mcp_request(body: dict) -> Optional[dict]:
    """
    Handle one JSON-RPC MCP message. Returns a response dict, or None for notifications.
    """
    if not isinstance(body, dict):
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32600, "message": "Invalid Request"},
        }

    req_id = body.get("id", None)
    method = body.get("method")
    params = body.get("params") or {}

    # Notifications have no id / no response
    is_notification = "id" not in body

    if method == "initialize":
        result = {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {
                "name": "AegisMCP",
                "version": settings.SERVICE_VERSION,
            },
        }
        if is_notification:
            return None
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    if method == "notifications/initialized":
        return None

    if method == "ping":
        if is_notification:
            return None
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}

    if method == "tools/list":
        if is_notification:
            return None
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}

    if method == "tools/call":
        name = params.get("name") or ""
        arguments = params.get("arguments") or {}
        tool_result = await _call_tool(name, arguments)
        if is_notification:
            return None
        return {"jsonrpc": "2.0", "id": req_id, "result": tool_result}

    if is_notification:
        return None

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }
