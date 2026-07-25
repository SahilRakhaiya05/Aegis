from fastapi import APIRouter, HTTPException, Query, Response

from app.domain.models import InvestigationReport, InvestigationRequest
from app.services import investigation as inv
from app.services.enrichment import enrich_payload
from app.services.evidence import collect_evidence
from app.services.investigation import resolve_window
from app.settings import settings

router = APIRouter()
legacy_router = APIRouter()


@router.post("", response_model=InvestigationReport)
@router.post("/", response_model=InvestigationReport)
async def run_investigation(request: InvestigationRequest):
    if not request.service:
        request.service = settings.OTEL_SERVICE_NAME
    return await inv.investigate(request)


@legacy_router.post("/analyze", response_model=InvestigationReport)
async def legacy_analyze(request: InvestigationRequest):
    if not request.service:
        request.service = settings.OTEL_SERVICE_NAME
    return await inv.investigate(request)


@router.post("/evidence")
async def fetch_evidence(request: InvestigationRequest):
    start_ms, end_ms = resolve_window(request)
    service = request.service or settings.OTEL_SERVICE_NAME
    bundle = await collect_evidence(
        service,
        start_ms,
        end_ms,
        include_alerts=request.include_alerts,
        include_services=request.include_services,
    )
    data = bundle.model_dump()
    extra = enrich_payload(bundle, None)
    data["timeline"] = extra["timeline"]
    data["trace_ids"] = extra["trace_ids"]
    data["highlights"] = extra["highlights"]
    data["signoz_queries"] = extra["signoz_queries"]
    data["signoz_links"] = extra["signoz_links"]
    return data


@router.get("/history")
async def investigation_history(limit: int = Query(default=20, ge=1, le=100)):
    items = await inv.get_history(limit)
    return {"items": [i.model_dump() for i in items], "count": len(items)}


@router.get("/history/{investigation_id}", response_model=InvestigationReport)
async def investigation_detail(investigation_id: str):
    report = await inv.get_report(investigation_id)
    if not report:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return report


@router.get("/history/{investigation_id}/export.md")
async def export_markdown(investigation_id: str):
    md = await inv.export_markdown(investigation_id)
    if not md:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return Response(
        content=md,
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="aegis-{investigation_id[:8]}.md"'
        },
    )


@router.get("/history/{investigation_id}/export.json")
async def export_json(investigation_id: str):
    report = await inv.get_report(investigation_id)
    if not report:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return report


@router.get("/stats")
async def probe_stats():
    return inv.session_stats()
