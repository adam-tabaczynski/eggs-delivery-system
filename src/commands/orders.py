from src.core.clock import Clock
from src.core.interfaces.unit_of_work import UnitOfWork
from src.exceptions import (
    CustomerNotFound,
    CycleAlreadyClosed,
    CycleNotFound,
    OpenOrderAlreadyExists,
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
        cycle = uow.cycles.get_for_update(cycle_id)
        if cycle is None:
            raise CycleNotFound()
        if cycle.effective_status(now) is DeliveryCycleStatus.CLOSED:
            raise CycleAlreadyClosed()
        open_order = uow.orders.get_open_order_for_customer(
            customer_id=customer_id, cycle_id=cycle_id
        )
        if open_order is not None:
            raise OpenOrderAlreadyExists()
        cycle.ensure_capacity(
            committed=uow.orders.sum_open_quantity(cycle_id),
            additional=quantity,
        )
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
        cycle = uow.cycles.get_for_update(order.cycle_id)
        if cycle is None:
            raise CycleNotFound()
        # Re-read after the lock: another writer may have changed this order
        # while we were waiting for it, and our in-memory copy is now stale.
        uow.orders.refresh(order)
        if cycle.effective_status(now) is DeliveryCycleStatus.CLOSED:
            raise CycleAlreadyClosed()
        if order.status is OrderStatus.CANCELLED:
            raise OrderAlreadyCancelled()
        if quantity is not None:
            cycle.ensure_capacity(
                committed=uow.orders.sum_open_quantity(
                    order.cycle_id, exclude_order_id=order.id
                ),
                additional=quantity,
            )
        uow.orders.update(order, quantity=quantity, status=status)
        uow.commit()
        return OrderRead.model_validate(order)
