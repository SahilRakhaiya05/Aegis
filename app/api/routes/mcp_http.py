"""HTTP transport for Aegis MCP."""

from __future__ import annotations

from typing import Any, Dict, List, Union

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.mcp.server import handle_mcp_request, aegis_mcp_info

router = APIRouter()


@router.get("/mcp")
async def mcp_info():
    """Discovery helper (not part of core MCP, useful for the UI)."""
    return {
        "ok": True,
        "endpoint": "/mcp",
        "method": "POST",
        "info": aegis_mcp_info(),
        "usage": {
            "initialize": {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            "tools_list": {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        },
    }


@router.post("/mcp")
async def mcp_post(request: Request):
    """Streamable-style HTTP MCP: accept one JSON-RPC object or a batch array."""
    try:
        body: Union[Dict[str, Any], List[Any]] = await request.json()
    except Exception:
        return JSONResponse(
            {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}},
            status_code=400,
        )

    if isinstance(body, list):
        results = []
        for item in body:
            if not isinstance(item, dict):
                continue
            resp = await handle_mcp_request(item)
            if resp is not None:
                results.append(resp)
        return JSONResponse(results if results else [])

    if not isinstance(body, dict):
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32600, "message": "Invalid Request"},
            },
            status_code=400,
        )

    resp = await handle_mcp_request(body)
    if resp is None:
        return JSONResponse({}, status_code=202)
    return JSONResponse(resp)
