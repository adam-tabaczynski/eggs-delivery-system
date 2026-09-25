import pytest

from src.core.exceptions import NotFoundError
from src.core.integrations.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from src.models import Order, OrderStatus
from tests.generators import make_customer, make_cycle, make_order, make_provider


class TestOrderRepository:
    def test_add_persists_defaults_and_timestamps(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()

        with SqlAlchemyUnitOfWork() as uow:
            order = uow.orders.add(
                Order(cycle_id=cycle.id, customer_id=customer.id, quantity=6)
            )
            uow.commit()
            order_id = order.id

        with SqlAlchemyUnitOfWork() as uow:
            stored = uow.orders.get(order_id)
            assert stored is not None
            assert stored.cycle_id == cycle.id
            assert stored.customer_id == customer.id
            assert stored.quantity == 6
            assert stored.status is OrderStatus.OPEN
            assert stored.created_at is not None
            assert stored.updated_at is not None

    def test_add_unknown_cycle(self) -> None:
        customer = make_customer()

        with pytest.raises(NotFoundError):
            with SqlAlchemyUnitOfWork() as uow:
                uow.orders.add(Order(cycle_id=0, customer_id=customer.id, quantity=6))
                uow.commit()

    def test_add_unknown_customer(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)

        with pytest.raises(NotFoundError):
            with SqlAlchemyUnitOfWork() as uow:
                uow.orders.add(Order(cycle_id=cycle.id, customer_id=0, quantity=6))
                uow.commit()

    def test_sum_open_quantity_excludes_cancelled_and_other_cycles(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        other_cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()
        make_order(cycle_id=cycle.id, customer_id=customer.id, quantity=4)
        make_order(
            cycle_id=cycle.id,
            customer_id=customer.id,
            quantity=6,
            status=OrderStatus.CANCELLED,
        )
        make_order(cycle_id=other_cycle.id, customer_id=customer.id, quantity=8)

        with SqlAlchemyUnitOfWork() as uow:
            assert uow.orders.sum_open_quantity(cycle.id) == 4
