from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

import app.api.routes.investigation as inv_routes
from app.domain.models import InvestigationReport
from app.main import app

client = TestClient(app)


def test_investigate_calls_service(monkeypatch):
    fake = InvestigationReport(
        summary="Inventory timeout under load.",
        affected_service="Aegis",
        root_cause="Downstream inventory timeout.",
        impact="Large orders failed.",
        suggested_resolution="Add circuit breaker.",
        evidence_source="signoz_mcp",
        llm_provider="offline",
        llm_model="aegis-offline",
        evidence_counts={"error_traces": 2, "error_logs": 1},
        confidence="medium",
    )
    mock = AsyncMock(return_value=fake)
    monkeypatch.setattr(inv_routes.inv, "investigate", mock)

    response = client.post(
        "/api/v1/investigate",
        json={"service": "Aegis", "lookback_minutes": 15},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["summary"] == fake.summary
    assert body["llm_provider"] in {"mock", "offline"}
    mock.assert_called_once()


def test_legacy_analyze_alias(monkeypatch):
    fake = InvestigationReport(
        summary="legacy ok",
        affected_service="Aegis",
        evidence_source="signoz_api",
        llm_provider="mock",
    )
    mock = AsyncMock(return_value=fake)
    monkeypatch.setattr(inv_routes.inv, "investigate", mock)
    response = client.post(
        "/api/v1/incidents/analyze",
        json={"service": "Aegis", "lookback_minutes": 10},
    )
    assert response.status_code == 200
    assert response.json()["summary"] == "legacy ok"


def test_chaos_latency():
    response = client.get("/api/v1/chaos/latency")
    assert response.status_code == 200
    assert response.json()["scenario"] == "latency"
