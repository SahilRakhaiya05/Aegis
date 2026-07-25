from fastapi import APIRouter

from app.api.routes import chaos, demo, investigation, system, workload

api_router = APIRouter()
api_router.include_router(system.router, tags=["system"])
api_router.include_router(chaos.router, prefix="/chaos", tags=["chaos"])
api_router.include_router(
    investigation.router, prefix="/investigate", tags=["investigate"]
)
api_router.include_router(
    workload.router, prefix="/workload/orders", tags=["workload"]
)
api_router.include_router(demo.router, prefix="/demo", tags=["demo"])

# Backward-compatible aliases for older scripts.
legacy = APIRouter()
legacy.include_router(chaos.router, prefix="/incidents", tags=["legacy"])
legacy.include_router(investigation.legacy_router, prefix="/incidents", tags=["legacy"])
legacy.include_router(workload.router, prefix="/orders", tags=["legacy"])
