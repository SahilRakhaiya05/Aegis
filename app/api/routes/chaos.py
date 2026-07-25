from fastapi import APIRouter, Query

from app.services import chaos as chaos_service

router = APIRouter()


@router.get("/error")
@router.get("/simulate-error")  # legacy alias path when mounted under /incidents
async def error():
    await chaos_service.simulate_error()


@router.get("/latency")
@router.get("/simulate-latency")
async def latency():
    return await chaos_service.simulate_latency()


@router.get("/flaky")
@router.get("/simulate-flaky")
async def flaky():
    return await chaos_service.simulate_flaky()


@router.post("/storm")
@router.get("/storm")
async def storm(count: int = Query(default=8, ge=1, le=30)):
    return await chaos_service.simulate_storm(count)
