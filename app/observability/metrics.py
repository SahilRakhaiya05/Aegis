from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

from app.observability.otlp import build_metric_exporter
from app.observability.resource import build_resource
from app.settings import settings


def configure_metrics() -> None:
    reader = PeriodicExportingMetricReader(
        build_metric_exporter(),
        export_interval_millis=max(1000, int(settings.OTEL_METRIC_EXPORT_INTERVAL)),
    )
    provider = MeterProvider(resource=build_resource(), metric_readers=[reader])
    metrics.set_meter_provider(provider)


def get_meter(name: str = "aegis"):
    return metrics.get_meter(name)
