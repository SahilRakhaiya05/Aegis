from fastapi import APIRouter, HTTPException

from app.domain.models import OrderCreate, OrderOut
from app.services import workload as workload_service

router = APIRouter()


@router.post("", response_model=OrderOut)
@router.post("/", response_model=OrderOut)
async def place_order(order: OrderCreate):
    try:
        return await workload_service.create_order(order)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("", response_model=list[OrderOut])
@router.get("/", response_model=list[OrderOut])
async def list_orders(limit: int = 50):
    return workload_service.list_orders(limit)


@router.get("/{order_id}", response_model=OrderOut)
async def read_order(order_id: str):
    order = await workload_service.get_order(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
