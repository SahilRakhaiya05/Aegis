import logging

from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

from app.observability.otlp import build_log_exporter
from app.observability.resource import build_resource


def configure_log_export() -> None:
    provider = LoggerProvider(resource=build_resource())
    provider.add_log_record_processor(BatchLogRecordProcessor(build_log_exporter()))
    set_logger_provider(provider)

    handler = LoggingHandler(level=logging.INFO, logger_provider=provider)
    root = logging.getLogger()
    for existing in list(root.handlers):
        if isinstance(existing, LoggingHandler):
            root.removeHandler(existing)
    root.addHandler(handler)
