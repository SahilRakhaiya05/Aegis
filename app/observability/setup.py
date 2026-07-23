"""Wire OpenTelemetry exporters + light instrumentation."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

from app.observability.logs_export import configure_log_export
from app.observability.metrics import configure_metrics
from app.observability.middleware import install_tracing_middleware
from app.observability.tracing import configure_tracing

logger = logging.getLogger(__name__)


def setup_observability(app: FastAPI | None = None) -> None:
    configure_tracing()
    configure_metrics()
    configure_log_export()

    try:
        RequestsInstrumentor().instrument()
    except Exception:
        logger.debug("Requests already instrumented", exc_info=True)
    try:
        LoggingInstrumentor().instrument(set_logging_format=True)
    except Exception:
        logger.debug("Logging already instrumented", exc_info=True)

    if app is not None:
        install_tracing_middleware(app)
