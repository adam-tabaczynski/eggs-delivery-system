import pytest

from src.commands.cycles import create_delivery_cycle
from src.core.clock import Clock
from src.core.exceptions import NotFoundError
from src.core.integrations.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from src.models import Order, OrderStatus
from tests.helpers import future_cycle_window


def test_order_persists(provider_id: int, customer_id: int) -> None:
    cutoff_at, delivery_at = future_cycle_window()
    cycle = create_delivery_cycle(
        provider_id=provider_id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=48,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )

    with SqlAlchemyUnitOfWork() as uow:
        created = uow.orders.add(
            Order(
                cycle_id=cycle.id,
                customer_id=customer_id,
                quantity=6,
                status=OrderStatus.OPEN,
            )
        )
        uow.commit()
        order_id = created.id

    with SqlAlchemyUnitOfWork() as uow:
        stored = uow.orders.get(order_id)
        assert stored is not None
        assert stored.cycle_id == cycle.id
        assert stored.customer_id == customer_id
        assert stored.quantity == 6
        assert stored.status == OrderStatus.OPEN
        assert stored.created_at is not None
        assert stored.updated_at is not None


def test_order_unknown_cycle(customer_id: int) -> None:
    with pytest.raises(NotFoundError, match="Referenced entity does not exist"):
        with SqlAlchemyUnitOfWork() as uow:
            uow.orders.add(
                Order(
                    cycle_id=0,
                    customer_id=customer_id,
                    quantity=6,
                    status=OrderStatus.OPEN,
                )
            )
            uow.commit()


def test_order_unknown_customer(provider_id: int) -> None:
    cutoff_at, delivery_at = future_cycle_window()
    cycle = create_delivery_cycle(
        provider_id=provider_id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=48,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )

    with pytest.raises(NotFoundError, match="Referenced entity does not exist"):
        with SqlAlchemyUnitOfWork() as uow:
            uow.orders.add(
                Order(
                    cycle_id=cycle.id,
                    customer_id=0,
                    quantity=6,
                    status=OrderStatus.OPEN,
                )
            )
            uow.commit()
