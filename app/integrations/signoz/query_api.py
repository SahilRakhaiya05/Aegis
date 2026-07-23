"""SigNoz Query Range REST client."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import httpx

from app.settings import settings

logger = logging.getLogger(__name__)


class SignozQueryClient:
    def __init__(self) -> None:
        self.base_url = settings.signoz_base_url
        self.timeout = settings.SIGNOZ_API_TIMEOUT_SECONDS

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if settings.SIGNOZ_API_KEY:
            headers["SIGNOZ-API-KEY"] = settings.SIGNOZ_API_KEY
            headers["Authorization"] = f"Bearer {settings.SIGNOZ_API_KEY}"
        return headers

    async def query_range(self, payload: dict) -> dict:
        url = f"{self.base_url}/api/v5/query_range"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload, headers=self._headers())
            if response.status_code >= 400:
                logger.error(
                    "query_range failed status=%s body=%s",
                    response.status_code,
                    response.text[:400],
                )
            response.raise_for_status()
            return response.json()

    @staticmethod
    def extract_rows(response: dict) -> List[dict]:
        extracted: List[dict] = []
        payload = response.get("data", {})
        if not isinstance(payload, dict):
            return extracted
        inner = payload.get("data", payload)
        if not isinstance(inner, dict):
            return extracted
        results = inner.get("results", [])
        if not isinstance(results, list):
            return extracted
        for result in results:
            if not isinstance(result, dict):
                continue
            for row in result.get("rows") or []:
                if not isinstance(row, dict):
                    continue
                record = row.get("data")
                if isinstance(record, dict):
                    if "timestamp" not in record and row.get("timestamp"):
                        record = {**record, "timestamp": row["timestamp"]}
                    extracted.append(record)
                else:
                    extracted.append(row)
            for key in ("series", "aggregations"):
                items = result.get(key) or []
                if isinstance(items, list):
                    extracted.extend(i for i in items if isinstance(i, dict))
        return extracted

    @staticmethod
    def as_dict_list(payload: Any) -> List[dict]:
        if payload is None:
            return []
        if isinstance(payload, list):
            return [x for x in payload if isinstance(x, dict)]
        if isinstance(payload, dict):
            for key in ("data", "results", "items", "traces", "logs", "rows", "spans"):
                inner = payload.get(key)
                if isinstance(inner, list):
                    return [x for x in inner if isinstance(x, dict)]
                if isinstance(inner, dict):
                    nested = SignozQueryClient.as_dict_list(inner)
                    if nested:
                        return nested
            return [payload]
        return []

    async def error_traces(
        self, service: str, start_ms: int, end_ms: int, limit: int = 20
    ) -> List[dict]:
        payload = {
            "start": start_ms,
            "end": end_ms,
            "requestType": "raw",
            "compositeQuery": {
                "queries": [
                    {
                        "type": "builder_query",
                        "spec": {
                            "name": "A",
                            "signal": "traces",
                            "filter": {
                                "expression": (
                                    f"serviceName = '{service}' AND hasError = true"
                                )
                            },
                            "selectFields": [
                                {"name": "serviceName"},
                                {"name": "name"},
                                {"name": "traceID"},
                                {"name": "spanID"},
                                {"name": "durationNano"},
                                {"name": "statusMessage"},
                            ],
                            "order": [
                                {"key": {"name": "timestamp"}, "direction": "desc"}
                            ],
                            "limit": limit,
                            "offset": 0,
                            "disabled": False,
                        },
                    }
                ]
            },
        }
        return self.extract_rows(await self.query_range(payload))

    async def error_logs(
        self, service: str, start_ms: int, end_ms: int, limit: int = 50
    ) -> List[dict]:
        payload = {
            "start": start_ms,
            "end": end_ms,
            "requestType": "raw",
            "compositeQuery": {
                "queries": [
                    {
                        "type": "builder_query",
                        "spec": {
                            "name": "A",
                            "signal": "logs",
                            "filter": {
                                "expression": (
                                    f"service.name = '{service}' "
                                    "AND severity_text IN ('ERROR', 'FATAL')"
                                )
                            },
                            "order": [
                                {"key": {"name": "timestamp"}, "direction": "desc"},
                                {"key": {"name": "id"}, "direction": "desc"},
                            ],
                            "limit": limit,
                            "offset": 0,
                            "disabled": False,
                        },
                    }
                ]
            },
        }
        return self.extract_rows(await self.query_range(payload))

    async def latency_p95(
        self, service: str, start_ms: int, end_ms: int, step_seconds: int = 60
    ) -> List[dict]:
        payload = {
            "start": start_ms,
            "end": end_ms,
            "requestType": "time_series",
            "compositeQuery": {
                "queries": [
                    {
                        "type": "builder_query",
                        "spec": {
                            "name": "A",
                            "signal": "metrics",
                            "stepInterval": step_seconds,
                            "aggregations": [
                                {
                                    "metricName": "signoz_latency",
                                    "spaceAggregation": "p95",
                                }
                            ],
                            "filter": {"expression": f"service.name = '{service}'"},
                            "disabled": False,
                        },
                    }
                ]
            },
        }
        return self.extract_rows(await self.query_range(payload))

    async def ping(self) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/version"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=self._headers())
                return {
                    "ok": response.status_code < 400,
                    "status_code": response.status_code,
                    "url": url,
                    "body_preview": response.text[:200],
                }
        except Exception as exc:
            return {"ok": False, "url": url, "error": str(exc)}


query_client = SignozQueryClient()
