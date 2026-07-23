"""Build deep links into the SigNoz Cloud UI."""

from __future__ import annotations

from urllib.parse import quote

from app.settings import settings


def base_url() -> str:
    return settings.signoz_base_url.rstrip("/")


def service_map() -> str:
    return f"{base_url()}/services"


def service_detail(service: str | None = None) -> str:
    name = service or settings.OTEL_SERVICE_NAME
    return f"{base_url()}/services/{quote(name, safe='')}"


def traces_explorer(service: str | None = None) -> str:
    name = service or settings.OTEL_SERVICE_NAME
    # SigNoz Cloud traces explorer; filter is applied in UI if pre-filter unsupported.
    return f"{base_url()}/traces-explorer?service={quote(name)}"


def logs_explorer(service: str | None = None) -> str:
    name = service or settings.OTEL_SERVICE_NAME
    return f"{base_url()}/logs/logs-explorer?service={quote(name)}"


def metrics_explorer() -> str:
    return f"{base_url()}/metrics-explorer/explorer"


def alerts() -> str:
    return f"{base_url()}/alerts"


def dashboards() -> str:
    return f"{base_url()}/dashboard"


def settings_ingestion() -> str:
    return f"{base_url()}/settings/ingestion-settings"


def all_links(service: str | None = None) -> dict:
    name = service or settings.OTEL_SERVICE_NAME
    return {
        "home": base_url(),
        "services": service_map(),
        "service": service_detail(name),
        "traces": traces_explorer(name),
        "logs": logs_explorer(name),
        "metrics": metrics_explorer(),
        "alerts": alerts(),
        "dashboards": dashboards(),
        "ingestion_settings": settings_ingestion(),
        "mcp": settings.SIGNOZ_MCP_URL,
        "otlp_endpoint": settings.otlp_endpoint,
        "service_name": name,
    }
