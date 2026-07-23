from fastapi import FastAPI, Request
from opentelemetry.trace import SpanKind, Status, StatusCode

from app.observability.tracing import get_tracer

tracer = get_tracer("aegis.http")


def install_tracing_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def tracing_middleware(request: Request, call_next):
        span_name = f"{request.method} {request.url.path}"
        with tracer.start_as_current_span(span_name, kind=SpanKind.SERVER) as span:
            span.set_attribute("http.request.method", request.method)
            span.set_attribute("url.path", request.url.path)
            span.set_attribute("http.route", request.url.path)
            try:
                response = await call_next(request)
                span.set_attribute("http.response.status_code", response.status_code)
                if response.status_code >= 500:
                    span.set_status(Status(StatusCode.ERROR))
                return response
            except Exception as exc:
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                raise
