from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class OrderCreate(BaseModel):
    item: str = Field(..., min_length=1, max_length=120)
    quantity: int = Field(..., gt=0, le=10_000)


class OrderOut(BaseModel):
    id: str
    item: str
    quantity: int
    status: str


class InvestigationRequest(BaseModel):
    service: str = Field(default="aegis")
    lookback_minutes: int = Field(default=30, ge=1, le=24 * 60)
    start_ms: Optional[int] = None
    end_ms: Optional[int] = None
    include_alerts: bool = True
    include_services: bool = False


class InvestigationReport(BaseModel):
    investigation_id: str = Field(default_factory=lambda: str(uuid4()))
    summary: Optional[str] = None
    affected_service: Optional[str] = None
    root_cause: Optional[str] = None
    impact: Optional[str] = None
    suggested_resolution: Optional[str] = None
    confidence: Optional[str] = None
    evidence_source: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    evidence_counts: Optional[Dict[str, Any]] = None
    created_at: str = Field(default_factory=utc_now_iso)
    window: Optional[Dict[str, int]] = None
    notes: Optional[List[str]] = None
    # Winning extras
    severity: Optional[Dict[str, Any]] = None
    timeline: Optional[List[Dict[str, Any]]] = None
    trace_ids: Optional[List[str]] = None
    signoz_queries: Optional[Dict[str, str]] = None
    signoz_links: Optional[Dict[str, str]] = None
    playbook: Optional[List[str]] = None
    highlights: Optional[Dict[str, Any]] = None
    duration_ms: Optional[float] = None


class EvidenceBundle(BaseModel):
    service: str
    window: Dict[str, int]
    evidence_source: str
    error_traces: List[Dict[str, Any]] = Field(default_factory=list)
    error_logs: List[Dict[str, Any]] = Field(default_factory=list)
    p95_latency_series: List[Dict[str, Any]] = Field(default_factory=list)
    alerts: List[Any] = Field(default_factory=list)
    services: List[Any] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
    counts: Dict[str, int] = Field(default_factory=dict)
    # UI-friendly summary
    timeline: Optional[List[Dict[str, Any]]] = None
    trace_ids: Optional[List[str]] = None
    highlights: Optional[Dict[str, Any]] = None


class ChaosResult(BaseModel):
    scenario: str
    status: str
    detail: str
    duration_ms: Optional[float] = None


class SystemStatus(BaseModel):
    status: str
    product: str
    version: str
    service: str
    llm_backend: str
    signoz_url: str
    signoz_mcp_url: str
    docs: str = "/docs"
    ui: str = "/"
