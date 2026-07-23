from __future__ import annotations

from typing import Any, Dict, Tuple

from app.settings import settings


def otlp_endpoint_and_headers() -> Tuple[str, Dict[str, str]]:
    return settings.otlp_endpoint, dict(settings.otlp_headers_dict)


def grpc_headers_tuple() -> Tuple[Tuple[str, str], ...]:
    return tuple(settings.otlp_headers_dict.items())


def is_insecure(endpoint: str) -> bool:
    return endpoint.lower().startswith("http://")


def _http_signal_endpoint(base: str, signal: str) -> str:
    cleaned = base.rstrip("/")
    for suffix in ("/v1/traces", "/v1/metrics", "/v1/logs"):
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)]
            break
    return f"{cleaned}/v1/{signal}"


def build_span_exporter() -> Any:
    endpoint, headers = otlp_endpoint_and_headers()
    if settings.OTEL_EXPORTER_OTLP_PROTOCOL == "grpc":
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )

        return OTLPSpanExporter(
            endpoint=endpoint,
            headers=grpc_headers_tuple() or None,
            insecure=is_insecure(endpoint),
        )
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

    return OTLPSpanExporter(
        endpoint=_http_signal_endpoint(endpoint, "traces"),
        headers=headers or None,
    )


def build_metric_exporter() -> Any:
    endpoint, headers = otlp_endpoint_and_headers()
    if settings.OTEL_EXPORTER_OTLP_PROTOCOL == "grpc":
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
            OTLPMetricExporter,
        )

        return OTLPMetricExporter(
            endpoint=endpoint,
            headers=grpc_headers_tuple() or None,
            insecure=is_insecure(endpoint),
        )
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
        OTLPMetricExporter,
    )

    return OTLPMetricExporter(
        endpoint=_http_signal_endpoint(endpoint, "metrics"),
        headers=headers or None,
    )


def build_log_exporter() -> Any:
    endpoint, headers = otlp_endpoint_and_headers()
    if settings.OTEL_EXPORTER_OTLP_PROTOCOL == "grpc":
        from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter

        return OTLPLogExporter(
            endpoint=endpoint,
            headers=grpc_headers_tuple() or None,
            insecure=is_insecure(endpoint),
        )
    from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter

    return OTLPLogExporter(
        endpoint=_http_signal_endpoint(endpoint, "logs"),
        headers=headers or None,
    )
