"""Persisted model generators for DB-backed tests."""

from datetime import datetime

from src.core.clock import Clock
from src.core.integrations.sqlalchemy.base import Base
from src.core.integrations.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from src.models import (
    Customer,
    DeliveryCycle,
    DeliveryCycleStatus,
    Order,
    OrderStatus,
    Provider,
)
from tests.helpers import unique_email


def _persist[T: Base](entity: T, uow: SqlAlchemyUnitOfWork) -> T:
    uow.commit()
    assert uow.session is not None
    uow.session.refresh(entity)
    uow.session.expunge(entity)
    return entity


def make_provider(*, name: str = "Test Farm", email: str | None = None) -> Provider:
    with SqlAlchemyUnitOfWork() as uow:
        provider = uow.providers.add(
            Provider(
                name=name,
                email=email if email is not None else unique_email("provider"),
            )
        )
        return _persist(provider, uow)


def make_customer(
    *,
    first_name: str = "Ada",
    last_name: str = "Lovelace",
    email: str | None = None,
) -> Customer:
    with SqlAlchemyUnitOfWork() as uow:
        customer = uow.customers.add(
            Customer(
                first_name=first_name,
                last_name=last_name,
                email=email if email is not None else unique_email("customer"),
            )
        )
        return _persist(customer, uow)


def make_cycle(
    *,
    provider_id: int,
    cutoff_at: datetime | None = None,
    delivery_at: datetime | None = None,
    max_eggs: int = 48,
    status: DeliveryCycleStatus = DeliveryCycleStatus.OPEN,
) -> DeliveryCycle:
    clock = Clock()
    with SqlAlchemyUnitOfWork() as uow:
        cycle = uow.cycles.add(
            DeliveryCycle(
                provider_id=provider_id,
                cutoff_at=(
                    cutoff_at
                    if cutoff_at is not None
                    else clock.move_datetime_forward(days=5)
                ),
                delivery_at=(
                    delivery_at
                    if delivery_at is not None
                    else clock.move_datetime_forward(days=7)
                ),
                max_eggs=max_eggs,
                status=status,
            )
        )
        return _persist(cycle, uow)


def make_order(
    *,
    cycle_id: int,
    customer_id: int,
    quantity: int = 6,
    status: OrderStatus = OrderStatus.OPEN,
) -> Order:
    with SqlAlchemyUnitOfWork() as uow:
        order = uow.orders.add(
            Order(
                cycle_id=cycle_id,
                customer_id=customer_id,
                quantity=quantity,
                status=status,
            )
        )
        return _persist(order, uow)
