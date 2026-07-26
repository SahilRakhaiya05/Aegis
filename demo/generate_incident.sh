#!/usr/bin/env bash
# Aegis demo traffic generator
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
SERVICE="${SERVICE:-aegis}"

echo "======================================"
echo " Aegis · demo traffic generator"
echo " Target: $BASE_URL"
echo " Service: $SERVICE"
echo "======================================"

echo
echo "[1/6] Warm-up"
for i in $(seq 1 8); do
  curl -s "$BASE_URL/" >/dev/null || true
  curl -s "$BASE_URL/api/v1/health" >/dev/null || true
  sleep 0.1
done
echo "  ok"

echo
echo "[2/6] Healthy orders"
for i in $(seq 1 12); do
  curl -s -X POST "$BASE_URL/api/v1/workload/orders" \
    -H "Content-Type: application/json" \
    -d '{"item":"widget","quantity":2}' >/dev/null || true
  sleep 0.1
done
echo "  ok"

echo
echo "[3/6] Risky orders (inventory fault path)"
for i in $(seq 1 10); do
  curl -s -X POST "$BASE_URL/api/v1/workload/orders" \
    -H "Content-Type: application/json" \
    -d '{"item":"bulk-kit","quantity":150}' >/dev/null || true
  sleep 0.15
done
echo "  ok"

echo
echo "[4/6] Fault injectors — error / flaky"
for i in $(seq 1 8); do
  curl -s "$BASE_URL/api/v1/chaos/error" >/dev/null || true
  curl -s "$BASE_URL/api/v1/chaos/flaky" >/dev/null || true
  sleep 0.15
done
echo "  ok"

echo
echo "[5/6] Latency + storm"
curl -s "$BASE_URL/api/v1/chaos/latency" >/dev/null || true
curl -s -X POST "$BASE_URL/api/v1/chaos/storm?count=8" >/dev/null || true
echo "  ok"

echo
echo "[6/6] Wait for SigNoz Cloud ingest (15s)"
sleep 15

echo
echo "Running probe…"
curl -s -X POST "$BASE_URL/api/v1/investigate" \
  -H "Content-Type: application/json" \
  -d "{\"service\":\"$SERVICE\",\"lookback_minutes\":30,\"include_alerts\":true}" \
  | python -m json.tool 2>/dev/null || curl -s -X POST "$BASE_URL/api/v1/investigate" \
  -H "Content-Type: application/json" \
  -d "{\"service\":\"$SERVICE\",\"lookback_minutes\":30}"

echo
echo "======================================"
echo " Demo traffic complete"
echo "======================================"
echo "Next:"
echo "  · UI:     $BASE_URL/"
echo "  · Health: $BASE_URL/api/v1/health/deep"
echo "  · SigNoz: filter service name = $SERVICE"
echo "  · MCP:    POST $BASE_URL/mcp"
