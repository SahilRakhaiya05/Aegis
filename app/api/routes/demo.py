"""One-click demo workflow: chaos → wait → investigate."""

from __future__ import annotations

import asyncio
import logging
import time

from fastapi import APIRouter, Query

from app.domain.models import InvestigationRequest
from app.services import chaos as chaos_service
from app.services import investigation as inv
from app.services import workload as workload_service
from app.domain.models import OrderCreate
from app.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/run")
async def run_demo(
    wait_seconds: float = Query(default=12, ge=0, le=60),
    lookback_minutes: int = Query(default=30, ge=5, le=180),
    storm_count: int = Query(default=6, ge=1, le=20),
):
    """
    Full demo path for judges:
    1) inject chaos + a risky order
    2) wait for SigNoz Cloud ingestion
    3) run investigation on `Aegis`
    """
    timeline = []
    t0 = time.perf_counter()

    # Chaos storm (logs only; no HTTP errors for storm)
    storm = await chaos_service.simulate_storm(storm_count)
    timeline.append({"step": "chaos_storm", "result": storm.model_dump()})

    # Force one explicit error path via logger-level simulation already in storm;
    # also try a large order that may fail.
    try:
        order = await workload_service.create_order(
            OrderCreate(item="demo-widget", quantity=150)
        )
        timeline.append({"step": "order", "result": order.model_dump()})
    except Exception as exc:
        timeline.append({"step": "order", "result": {"failed": True, "detail": str(exc)}})
        logger.error("Demo order failed as expected path: %s", exc)

    # Short latency blip
    lat = await chaos_service.simulate_latency()
    timeline.append({"step": "latency", "result": lat.model_dump()})

    if wait_seconds > 0:
        timeline.append({"step": "wait_ingestion", "seconds": wait_seconds})
        await asyncio.sleep(wait_seconds)

    report = await inv.investigate(
        InvestigationRequest(
            service=settings.OTEL_SERVICE_NAME,
            lookback_minutes=lookback_minutes,
            include_alerts=True,
            include_services=True,
        )
    )
    timeline.append(
        {
            "step": "investigate",
            "investigation_id": report.investigation_id,
            "evidence_source": report.evidence_source,
            "llm_provider": report.llm_provider,
        }
    )

    return {
        "ok": True,
        "duration_ms": round((time.perf_counter() - t0) * 1000, 1),
        "timeline": timeline,
        "report": report.model_dump(),
        "signoz_service": settings.OTEL_SERVICE_NAME,
        "hint": "Open the UI history panel or SigNoz Traces explorer for service Aegis.",
    }
