"""SigNoz Cloud hosted MCP client (streamable HTTP + header auth)."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

import httpx

from app.settings import settings

logger = logging.getLogger(__name__)


class SignozMCPError(RuntimeError):
    pass


class SignozMCPClient:
    def __init__(
        self,
        mcp_url: Optional[str] = None,
        api_key: Optional[str] = None,
        signoz_url: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        self.mcp_url = (mcp_url or settings.SIGNOZ_MCP_URL).rstrip("/")
        self.api_key = api_key if api_key is not None else settings.SIGNOZ_API_KEY
        self.signoz_url = (signoz_url or settings.signoz_base_url).rstrip("/")
        self.timeout = timeout or settings.SIGNOZ_MCP_TIMEOUT_SECONDS
        self._session_id: Optional[str] = None
        self._request_id = 0
        self._initialized = False

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.api_key:
            headers["SIGNOZ-API-KEY"] = self.api_key
        if self.signoz_url:
            headers["X-SigNoz-URL"] = self.signoz_url
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id
        return headers

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def _parse_sse(self, text: str) -> Any:
        last: Any = {}
        for line in text.splitlines():
            line = line.strip()
            if not line.startswith("data:"):
                continue
            raw = line[5:].strip()
            if not raw or raw == "[DONE]":
                continue
            try:
                last = json.loads(raw)
            except json.JSONDecodeError:
                continue
        return last

    def _parse_body(self, response: httpx.Response) -> Any:
        content_type = (response.headers.get("content-type") or "").lower()
        text = response.text or ""
        if "text/event-stream" in content_type or text.lstrip().startswith("event:"):
            return self._parse_sse(text)
        if not text.strip():
            return {}
        try:
            return response.json()
        except Exception:
            return self._parse_sse(text)

    async def _post_rpc(self, method: str, params: Optional[dict] = None) -> Any:
        payload: Dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
        }
        if params is not None:
            payload["params"] = params

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.mcp_url, headers=self._headers(), json=payload
            )
            session = response.headers.get("mcp-session-id") or response.headers.get(
                "Mcp-Session-Id"
            )
            if session:
                self._session_id = session
            if response.status_code >= 400:
                raise SignozMCPError(
                    f"MCP HTTP {response.status_code}: {response.text[:500]}"
                )
            data = self._parse_body(response)
            if isinstance(data, dict) and data.get("error"):
                raise SignozMCPError(f"MCP error: {data['error']}")
            if isinstance(data, dict) and "result" in data:
                return data["result"]
            return data

    async def _notify(self, method: str, params: dict) -> None:
        payload = {"jsonrpc": "2.0", "method": method, "params": params}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            await client.post(self.mcp_url, headers=self._headers(), json=payload)

    async def initialize(self) -> dict:
        result = await self._post_rpc(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": settings.APP_NAME,
                    "version": settings.SERVICE_VERSION,
                },
            },
        )
        try:
            await self._notify("notifications/initialized", {})
        except Exception:
            logger.debug("MCP notifications/initialized failed", exc_info=True)
        self._initialized = True
        return result if isinstance(result, dict) else {"raw": result}

    async def ensure_initialized(self) -> None:
        if not self._initialized:
            await self.initialize()

    async def list_tools(self) -> List[dict]:
        await self.ensure_initialized()
        result = await self._post_rpc("tools/list", {})
        if isinstance(result, dict):
            tools = result.get("tools") or []
            return tools if isinstance(tools, list) else []
        return []

    def _normalize_tool_result(self, result: Any) -> Any:
        if not isinstance(result, dict):
            return result
        if result.get("isError"):
            raise SignozMCPError(f"Tool error: {result}")
        content = result.get("content")
        if isinstance(content, list) and content:
            texts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    texts.append(item.get("text") or "")
            joined = "\n".join(t for t in texts if t)
            if joined:
                try:
                    return json.loads(joined)
                except json.JSONDecodeError:
                    return {"text": joined}
        return result

    async def call_tool(self, name: str, arguments: Optional[dict] = None) -> Any:
        await self.ensure_initialized()
        result = await self._post_rpc(
            "tools/call", {"name": name, "arguments": arguments or {}}
        )
        return self._normalize_tool_result(result)

    async def _first_tool(self, names: List[str], args: dict) -> Any:
        last_err: Optional[Exception] = None
        for name in names:
            try:
                return await self.call_tool(name, args)
            except SignozMCPError as exc:
                last_err = exc
                logger.debug("MCP tool %s failed: %s", name, exc)
        raise SignozMCPError(str(last_err or "No MCP tool succeeded"))

    async def search_traces(
        self,
        service: str,
        start_ms: int,
        end_ms: int,
        *,
        errors_only: bool = True,
        limit: int = 20,
    ) -> Any:
        args = {
            "service": service,
            "serviceName": service,
            "start": start_ms,
            "end": end_ms,
            "startMs": start_ms,
            "endMs": end_ms,
            "limit": limit,
            "hasError": errors_only,
            "query": f"serviceName = '{service}'"
            + (" AND hasError = true" if errors_only else ""),
        }
        return await self._first_tool(["signoz_search_traces", "search_traces"], args)

    async def search_logs(
        self, service: str, start_ms: int, end_ms: int, *, limit: int = 50
    ) -> Any:
        args = {
            "service": service,
            "serviceName": service,
            "start": start_ms,
            "end": end_ms,
            "startMs": start_ms,
            "endMs": end_ms,
            "limit": limit,
            "severity": "ERROR",
            "query": (
                f"service.name = '{service}' AND severity_text IN ('ERROR','FATAL')"
            ),
        }
        return await self._first_tool(["signoz_search_logs", "search_logs"], args)

    async def get_trace_details(self, trace_id: str) -> Any:
        args = {"traceId": trace_id, "traceID": trace_id, "trace_id": trace_id}
        return await self._first_tool(
            ["signoz_get_trace_details", "get_trace_details"], args
        )

    async def list_alerts(self) -> Any:
        try:
            return await self._first_tool(["signoz_list_alerts", "list_alerts"], {})
        except SignozMCPError:
            return []

    async def list_services(self, start_ms: int, end_ms: int) -> Any:
        args = {"start": start_ms, "end": end_ms, "startMs": start_ms, "endMs": end_ms}
        return await self._first_tool(
            ["signoz_list_services", "list_services"], args
        )

    async def health_check(self) -> Dict[str, Any]:
        try:
            init = await self.initialize()
            tools = await self.list_tools()
            names = [
                t.get("name") for t in tools if isinstance(t, dict) and t.get("name")
            ]
            return {
                "ok": True,
                "tool_count": len(names),
                "tools_sample": names[:15],
                "server": (init or {}).get("serverInfo")
                if isinstance(init, dict)
                else None,
            }
        except Exception as exc:
            logger.warning("MCP health failed: %s", exc)
            return {"ok": False, "error": str(exc)}


async def mcp_health() -> Dict[str, Any]:
    return await SignozMCPClient().health_check()
