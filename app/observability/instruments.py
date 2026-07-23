"""Business metrics for the demo workload — created lazily after MeterProvider is set."""

from __future__ import annotations

from typing import Any

from app.observability.metrics import get_meter

_meter = None
_orders_created = None
_order_failures = None
_order_duration = None
_investigations = None
_chaos_events = None


def _ensure() -> Any:
    global _meter, _orders_created, _order_failures, _order_duration
    global _investigations, _chaos_events
    if _meter is None:
        _meter = get_meter("aegis.workload")
        _orders_created = _meter.create_counter(
            "aegis.orders.created", unit="1", description="Orders created"
        )
        _order_failures = _meter.create_counter(
            "aegis.orders.failures", unit="1", description="Order failures"
        )
        _order_duration = _meter.create_histogram(
            "aegis.orders.duration_ms", unit="ms", description="Order latency"
        )
        _investigations = _meter.create_counter(
            "aegis.investigations.total", unit="1", description="Investigations"
        )
        _chaos_events = _meter.create_counter(
            "aegis.chaos.events", unit="1", description="Chaos events"
        )
    return _meter


class _CounterProxy:
    def __init__(self, attr: str):
        self.attr = attr

    def add(self, amount: int = 1, attributes: dict | None = None) -> None:
        _ensure()
        getattr(globals()[self.attr], "add")(amount, attributes or {})


class _HistProxy:
    def record(self, amount: float, attributes: dict | None = None) -> None:
        _ensure()
        _order_duration.record(amount, attributes or {})


# Module-level names used by services
class _OrdersCreated:
    def add(self, amount: int = 1, attributes: dict | None = None) -> None:
        _ensure()
        _orders_created.add(amount, attributes or {})


class _OrderFailures:
    def add(self, amount: int = 1, attributes: dict | None = None) -> None:
        _ensure()
        _order_failures.add(amount, attributes or {})


class _Investigations:
    def add(self, amount: int = 1, attributes: dict | None = None) -> None:
        _ensure()
        _investigations.add(amount, attributes or {})


class _ChaosEvents:
    def add(self, amount: int = 1, attributes: dict | None = None) -> None:
        _ensure()
        _chaos_events.add(amount, attributes or {})


orders_created_total = _OrdersCreated()
order_failures_total = _OrderFailures()
order_creation_duration = _HistProxy()
investigations_total = _Investigations()
chaos_events_total = _ChaosEvents()
