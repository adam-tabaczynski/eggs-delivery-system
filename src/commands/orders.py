from src.core.clock import Clock
from src.core.interfaces.unit_of_work import UnitOfWork
from src.exceptions import (
    CycleAlreadyClosed,
    CycleNotFound,
    CustomerNotFound,
    OrderAlreadyCancelled,
    OrderNotFound,
)
from src.models import DeliveryCycleStatus, Order, OrderStatus
from src.schemas import OrderRead


def place_order(
    *,
    customer_id: int,
    cycle_id: int,
    quantity: int,
    uow: UnitOfWork,
    clock: Clock,
) -> OrderRead:
    now = clock.datetime_now()
    with uow:
        if uow.customers.get(customer_id) is None:
            raise CustomerNotFound()
        cycle = uow.cycles.get(cycle_id)
        if cycle is None:
            raise CycleNotFound()
        if cycle.effective_status(now) is DeliveryCycleStatus.CLOSED:
            raise CycleAlreadyClosed()
        order = Order(
            cycle_id=cycle_id,
            customer_id=customer_id,
            quantity=quantity,
            status=OrderStatus.OPEN,
        )
        uow.orders.add(order)
        uow.commit()
        return OrderRead.model_validate(order)


def update_order(
    *,
    customer_id: int,
    order_id: int,
    quantity: int | None = None,
    status: OrderStatus | None = None,
    uow: UnitOfWork,
    clock: Clock,
) -> OrderRead:
    now = clock.datetime_now()
    with uow:
        if uow.customers.get(customer_id) is None:
            raise CustomerNotFound()
        order = uow.orders.get(order_id)
        if order is None or order.customer_id != customer_id:
            raise OrderNotFound()
        cycle = uow.cycles.get(order.cycle_id)
        if cycle is None:
            raise CycleNotFound()
        if cycle.effective_status(now) is DeliveryCycleStatus.CLOSED:
            raise CycleAlreadyClosed()
        if order.status is OrderStatus.CANCELLED:
            raise OrderAlreadyCancelled()
        uow.orders.update(order, quantity=quantity, status=status)
        uow.commit()
        return OrderRead.model_validate(order)
