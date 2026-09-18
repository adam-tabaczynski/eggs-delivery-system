from fastapi import APIRouter, Depends, status

from src.commands.orders import place_order, update_order
from src.core.clock import Clock
from src.core.interfaces.unit_of_work import UnitOfWork
from src.dependencies import get_clock, get_uow
from src.queries.orders import list_orders_for_customer
from src.schemas import OrderCreate, OrderRead, OrderUpdate

router = APIRouter()


@router.post(
    "/customers/{customer_id}/orders",
    status_code=status.HTTP_201_CREATED,
)
def create_order(
    customer_id: int,
    body: OrderCreate,
    uow: UnitOfWork = Depends(get_uow),
    clock: Clock = Depends(get_clock),
) -> OrderRead:
    return place_order(
        customer_id=customer_id,
        cycle_id=body.cycle_id,
        quantity=body.quantity,
        uow=uow,
        clock=clock,
    )


@router.get("/customers/{customer_id}/orders")
def list_customer_orders(
    customer_id: int,
    uow: UnitOfWork = Depends(get_uow),
) -> list[OrderRead]:
    return list_orders_for_customer(customer_id=customer_id, uow=uow)


@router.patch("/customers/{customer_id}/orders/{order_id}")
def patch_order(
    customer_id: int,
    order_id: int,
    body: OrderUpdate,
    uow: UnitOfWork = Depends(get_uow),
    clock: Clock = Depends(get_clock),
) -> OrderRead:
    return update_order(
        customer_id=customer_id,
        order_id=order_id,
        quantity=body.quantity,
        status=body.status,
        uow=uow,
        clock=clock,
    )
