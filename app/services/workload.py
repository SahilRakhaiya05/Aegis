"""Demo commerce workload with intentional inventory fault."""

from __future__ import annotations

import logging
import random
import time
import uuid
from typing import Dict, Optional

from app.domain.models import OrderCreate, OrderOut
from app.observability.instruments import (
    order_creation_duration,
    order_failures_total,
    orders_created_total,
)

logger = logging.getLogger(__name__)
_ORDERS: Dict[str, OrderOut] = {}


async def create_order(order: OrderCreate) -> OrderOut:
    start = time.perf_counter()
    if order.quantity > 100 and random.random() < 0.35:
        order_failures_total.add(1, {"reason": "inventory_timeout"})
        logger.error(
            "Order creation failed: inventory service timeout",
            extra={"item": order.item, "quantity": order.quantity},
        )
        raise RuntimeError("Inventory service timeout while reserving stock")

    order_id = str(uuid.uuid4())
    result = OrderOut(
        id=order_id, item=order.item, quantity=order.quantity, status="confirmed"
    )
    _ORDERS[order_id] = result
    orders_created_total.add(1, {"item": order.item})
    order_creation_duration.record((time.perf_counter() - start) * 1000)
    logger.info("Order created", extra={"order_id": order_id, "item": order.item})
    return result


async def get_order(order_id: str) -> Optional[OrderOut]:
    return _ORDERS.get(order_id)


def list_orders(limit: int = 50) -> list[OrderOut]:
    items = list(_ORDERS.values())
    return items[-limit:]
