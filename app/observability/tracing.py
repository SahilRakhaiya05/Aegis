from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.observability.otlp import build_span_exporter
from app.observability.resource import build_resource


def configure_tracing() -> None:
    provider = TracerProvider(resource=build_resource())
    provider.add_span_processor(BatchSpanProcessor(build_span_exporter()))
    trace.set_tracer_provider(provider)


def get_tracer(name: str = "aegis"):
    return trace.get_tracer(name)
