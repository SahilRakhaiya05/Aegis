from fastapi import APIRouter, Query

from app.integrations.llm.router import resolve_backend
from app.integrations.signoz import links as signoz_links
from app.integrations.signoz.mcp import SignozMCPClient, mcp_health
from app.integrations.signoz.query_api import query_client
from app.mcp.server import aegis_mcp_info
from app.settings import settings

router = APIRouter()


def _reasoner_label() -> str:
    """UI-safe label — never surface vendor model brand names."""
    backend = resolve_backend()
    if backend == "mock":
        return "offline"
    return "online"


@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "product": settings.PRODUCT_TITLE,
        "service": settings.OTEL_SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "reasoner": _reasoner_label(),
        "signoz_url": settings.signoz_base_url,
        "mcp": {
            "signoz": settings.SIGNOZ_MCP_URL,
            "aegis": "/mcp",
        },
    }


@router.get("/health/deep")
async def health_deep():
    api = await query_client.ping()
    smcp = (
        await mcp_health()
        if settings.SIGNOZ_USE_MCP
        else {"ok": False, "skipped": True}
    )
    aegis_mcp = aegis_mcp_info()
    overall = "healthy" if api.get("ok") or smcp.get("ok") else "degraded"
    return {
        "status": overall,
        "product": settings.PRODUCT_TITLE,
        "service": settings.OTEL_SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "environment": settings.deployment_environment,
        "signoz": {
            "url": settings.signoz_base_url,
            "api": api,
            "mcp_url": settings.SIGNOZ_MCP_URL,
            "mcp": smcp,
            "links": signoz_links.all_links(),
        },
        "mcp": {
            "signoz": {
                "url": settings.SIGNOZ_MCP_URL,
                "ok": bool(smcp.get("ok")),
                "tool_count": smcp.get("tool_count"),
                "server": smcp.get("server"),
            },
            "aegis": {
                "url": aegis_mcp["url"],
                "ok": True,
                "tool_count": aegis_mcp["tool_count"],
                "server": {"name": aegis_mcp["name"], "version": aegis_mcp["version"]},
                "tools": aegis_mcp["tools"],
            },
        },
        "otel": {
            "endpoint": settings.otlp_endpoint,
            "protocol": settings.OTEL_EXPORTER_OTLP_PROTOCOL,
            "headers_configured": bool(settings.otlp_headers_dict),
            "service_name": settings.OTEL_SERVICE_NAME,
        },
        "reasoner": {
            "status": _reasoner_label(),
            "ready": resolve_backend() != "mock" or True,
        },
    }


@router.get("/meta")
async def meta():
    return {
        "product": settings.PRODUCT_TITLE,
        "service": settings.OTEL_SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "environment": settings.deployment_environment,
        "signoz_url": settings.signoz_base_url,
        "signoz_mcp_url": settings.SIGNOZ_MCP_URL,
        "aegis_mcp_url": "/mcp",
        "signoz_links": signoz_links.all_links(),
        "reasoner": _reasoner_label(),
        "docs": "/docs",
        "ui": "/",
        "endpoints": {
            "health": "/api/v1/health",
            "health_deep": "/api/v1/health/deep",
            "signoz_links": "/api/v1/signoz/links",
            "signoz_mcp_tools": "/api/v1/signoz/mcp/tools",
            "aegis_mcp": "/mcp",
            "aegis_mcp_tools": "/api/v1/mcp/tools",
            "investigate": "/api/v1/investigate",
            "evidence": "/api/v1/investigate/evidence",
            "history": "/api/v1/investigate/history",
            "stats": "/api/v1/investigate/stats",
            "export_md": "/api/v1/investigate/history/{id}/export.md",
            "demo_run": "/api/v1/demo/run",
        },
    }


@router.get("/signoz/links")
async def get_signoz_links(service: str | None = Query(default=None)):
    return {
        "instance": settings.signoz_base_url,
        "links": signoz_links.all_links(service),
    }


@router.get("/signoz/mcp/tools")
async def list_signoz_mcp_tools():
    if not settings.SIGNOZ_USE_MCP:
        return {"ok": False, "source": "signoz", "tools": [], "error": "MCP disabled"}
    client = SignozMCPClient()
    try:
        await client.initialize()
        tools = await client.list_tools()
        names = [
            {
                "name": t.get("name"),
                "description": (t.get("description") or "")[:240],
            }
            for t in tools
            if isinstance(t, dict) and t.get("name")
        ]
        return {
            "ok": True,
            "source": "signoz",
            "mcp_url": settings.SIGNOZ_MCP_URL,
            "count": len(names),
            "tools": names,
        }
    except Exception as exc:
        return {
            "ok": False,
            "source": "signoz",
            "mcp_url": settings.SIGNOZ_MCP_URL,
            "error": str(exc),
        }


@router.get("/mcp/tools")
async def list_aegis_mcp_tools():
    info = aegis_mcp_info()
    from app.mcp.server import TOOLS

    return {
        "ok": True,
        "source": "aegis",
        "mcp_url": "/mcp",
        "count": len(TOOLS),
        "tools": [
            {
                "name": t["name"],
                "description": t.get("description", ""),
            }
            for t in TOOLS
        ],
        "server": {"name": info["name"], "version": info["version"]},
    }
