"""In-memory investigation history (demo-friendly)."""

from __future__ import annotations

from collections import deque
from threading import Lock
from typing import Deque, List, Optional

from app.domain.models import InvestigationReport
from app.settings import settings

_lock = Lock()
_history: Deque[InvestigationReport] = deque(maxlen=settings.MAX_HISTORY_ITEMS)


def push(report: InvestigationReport) -> None:
    with _lock:
        _history.appendleft(report)


def list_reports(limit: int = 20) -> List[InvestigationReport]:
    with _lock:
        return list(_history)[: max(1, min(limit, settings.MAX_HISTORY_ITEMS))]


def get(investigation_id: str) -> Optional[InvestigationReport]:
    with _lock:
        for item in _history:
            if item.investigation_id == investigation_id:
                return item
    return None


def clear() -> None:
    with _lock:
        _history.clear()
