from app.domain.models import EvidenceBundle
from app.services.enrichment import enrich_payload, report_to_markdown, severity_score


def test_severity_score_critical():
    s = severity_score({"error_traces": 5, "error_logs": 4, "alerts": 2}, "high")
    assert s["score"] >= 70
    assert s["label"] == "critical"


def test_enrich_payload_has_timeline():
    bundle = EvidenceBundle(
        service="aegis",
        window={"start_ms": 1, "end_ms": 2},
        evidence_source="signoz_mcp",
        error_traces=[{"name": "GET /x", "traceID": "abc", "statusMessage": "boom"}],
        error_logs=[{"severity_text": "ERROR", "body": "fail"}],
        counts={"error_traces": 1, "error_logs": 1, "alerts": 0},
    )
    extra = enrich_payload(bundle, "medium")
    assert extra["severity"]["score"] > 0
    assert extra["timeline"]
    assert "abc" in extra["trace_ids"]
    assert extra["playbook"]
    assert extra["signoz_queries"]["service_filter"] == "aegis"


def test_markdown_export():
    md = report_to_markdown(
        {
            "investigation_id": "id-1",
            "affected_service": "aegis",
            "summary": "sum",
            "root_cause": "rc",
            "impact": "imp",
            "suggested_resolution": "fix",
            "confidence": "high",
            "evidence_source": "signoz_mcp",
            "severity": {"label": "elevated", "score": 50},
            "playbook": ["step one"],
        }
    )
    assert "# Aegis investigation" in md
    assert "step one" in md
