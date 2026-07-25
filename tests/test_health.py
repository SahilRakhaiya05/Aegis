from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["product"] == "Aegis"
    assert "reasoner" in body or "mcp" in body


def test_aegis_mcp_tools():
    response = client.get("/api/v1/mcp/tools")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["count"] >= 1
    names = {t["name"] for t in body["tools"]}
    assert "aegis_investigate" in names


def test_aegis_mcp_initialize():
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "0"},
            },
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["result"]["serverInfo"]["name"] == "AegisMCP"


def test_meta():
    response = client.get("/api/v1/meta")
    assert response.status_code == 200
    assert response.json()["product"] == "Aegis"


def test_ui_home():
    response = client.get("/")
    assert response.status_code == 200
    assert "Aegis" in response.text


def test_signoz_links():
    response = client.get("/api/v1/signoz/links")
    assert response.status_code == 200
    body = response.json()
    assert "links" in body
    assert "home" in body["links"]
    assert "traces" in body["links"]
    assert body["links"]["service_name"] == "aegis"
