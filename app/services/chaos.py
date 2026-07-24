"""Chaos / incident simulation scenarios for demos."""

from __future__ import annotations

import asyncio
import logging
import random
import time

from fastapi import HTTPException

from app.domain.models import ChaosResult
from app.observability.instruments import chaos_events_total

logger = logging.getLogger(__name__)


async def simulate_error() -> None:
    chaos_events_total.add(1, {"scenario": "error"})
    logger.error(
        "Chaos: simulated downstream dependency failure",
        extra={"scenario": "error"},
    )
    raise HTTPException(
        status_code=500, detail="Simulated downstream dependency failure"
    )


async def simulate_latency() -> ChaosResult:
    delay = random.uniform(2.0, 5.0)
    chaos_events_total.add(1, {"scenario": "latency"})
    logger.warning(
        "Chaos: simulating latency",
        extra={"scenario": "latency", "delay_seconds": round(delay, 2)},
    )
    started = time.perf_counter()
    await asyncio.sleep(delay)
    return ChaosResult(
        scenario="latency",
        status="ok",
        detail=f"Completed after {delay:.2f}s delay",
        duration_ms=round((time.perf_counter() - started) * 1000, 1),
    )


async def simulate_flaky() -> ChaosResult:
    chaos_events_total.add(1, {"scenario": "flaky"})
    if random.random() < 0.5:
        logger.warning("Chaos: flaky failure", extra={"scenario": "flaky"})
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
    return ChaosResult(
        scenario="flaky",
        status="ok",
        detail="OK this time",
    )


async def simulate_storm(count: int = 8) -> ChaosResult:
    """Fire a burst of mixed chaos for richer SigNoz evidence."""
    count = max(1, min(count, 30))
    chaos_events_total.add(count, {"scenario": "storm"})
    errors = 0
    ok = 0
    for i in range(count):
        choice = random.choice(["error", "flaky", "latency_short", "ok"])
        if choice == "error":
            logger.error("Chaos storm error #%s", i + 1)
            errors += 1
        elif choice == "flaky":
            logger.warning("Chaos storm flaky #%s", i + 1)
            errors += 1
        elif choice == "latency_short":
            await asyncio.sleep(random.uniform(0.05, 0.2))
            ok += 1
        else:
            logger.info("Chaos storm ok #%s", i + 1)
            ok += 1
    return ChaosResult(
        scenario="storm",
        status="ok",
        detail=f"Storm finished: injected_logs={count} errors={errors} ok={ok}",
    )
