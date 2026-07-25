"""Aegis MCP protocol tests."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_mcp_info_get():
    r = client.get("/mcp")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["info"]["name"] == "AegisMCP"
    assert "aegis_investigate" in body["info"]["tools"]


def test_mcp_tools_list():
    r = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    )
    assert r.status_code == 200
    tools = r.json()["result"]["tools"]
    names = {t["name"] for t in tools}
    assert "aegis_health" in names
    assert "aegis_investigate" in names
    assert "aegis_evidence" in names


def test_mcp_signoz_links_tool():
    r = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "aegis_signoz_links",
                "arguments": {"service": "aegis"},
            },
        },
    )
    assert r.status_code == 200
    result = r.json()["result"]
    assert result.get("isError") is False
    text = result["content"][0]["text"]
    assert "aegis" in text or "signoz" in text.lower()


def test_api_mcp_tools_alias():
    r = client.get("/api/v1/mcp/tools")
    assert r.status_code == 200
    assert r.json()["source"] == "aegis"
    assert r.json()["count"] >= 6
