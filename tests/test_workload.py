"""Workload and chaos smoke tests."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_place_small_order():
    r = client.post(
        "/api/v1/workload/orders",
        json={"item": "bolt", "quantity": 2},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["item"] == "bolt"
    assert body["status"] == "confirmed"
    assert body["id"]


def test_list_orders():
    client.post("/api/v1/workload/orders", json={"item": "nut", "quantity": 1})
    r = client.get("/api/v1/workload/orders")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_chaos_storm():
    r = client.post("/api/v1/chaos/storm?count=3")
    assert r.status_code == 200
    assert r.json()["scenario"] == "storm"


def test_legacy_orders_alias():
    r = client.post("/api/v1/orders", json={"item": "legacy", "quantity": 1})
    assert r.status_code == 200
