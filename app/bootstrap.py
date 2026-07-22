"""Application factory for Aegis."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import __product__, __version__
from app.api.router import api_router, legacy
from app.api.routes import mcp_http
from app.logging_setup import configure_logging
from app.observability.setup import setup_observability
from app.settings import settings

WEB_DIR = Path(__file__).resolve().parent / "web"
STATIC_DIR = WEB_DIR / "static"
TEMPLATES_DIR = WEB_DIR / "templates"


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title=settings.PRODUCT_TITLE,
        version=settings.SERVICE_VERSION or __version__,
        description=(
            f"{__product__} — SRE copilot on SigNoz Cloud. "
            "OpenTelemetry telemetry, SigNoz MCP evidence, Aegis MCP tools, "
            "and structured root-cause reports."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Observability must run before route handlers generate metrics.
    setup_observability(app)

    app.include_router(api_router, prefix="/api/v1")
    app.include_router(legacy, prefix="/api/v1")
    # Aegis MCP at /mcp (and discovery helpers under /api/v1 already cover tools)
    app.include_router(mcp_http.router)

    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/api")
    async def api_index():
        return {
            "product": settings.PRODUCT_TITLE,
            "version": settings.SERVICE_VERSION,
            "docs": "/docs",
            "ui": "/",
            "health": "/api/v1/health",
            "aegis_mcp": "/mcp",
            "signoz_mcp": settings.SIGNOZ_MCP_URL,
        }

    @app.get("/")
    async def ui_home():
        index = TEMPLATES_DIR / "index.html"
        if index.exists():
            return FileResponse(index)
        return {
            "product": settings.PRODUCT_TITLE,
            "status": "ok",
            "docs": "/docs",
        }

    return app
