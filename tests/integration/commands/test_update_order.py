import pytest

from src.commands.orders import update_order
from src.core.clock import Clock
from src.core.integrations.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from src.exceptions import (
    CustomerNotFound,
    CycleAlreadyClosed,
    CycleCapacityExceeded,
    OrderAlreadyCancelled,
    OrderNotFound,
)
from src.models import DeliveryCycleStatus, OrderStatus
from tests.generators import make_customer, make_cycle, make_order, make_provider


class TestUpdateOrder:
    def test_updates_quantity(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()
        order = make_order(cycle_id=cycle.id, customer_id=customer.id, quantity=6)
        quantity = 12

        result = update_order(
            customer_id=customer.id,
            order_id=order.id,
            quantity=quantity,
            uow=SqlAlchemyUnitOfWork(),
            clock=Clock(),
        )

        assert result.id == order.id
        assert result.quantity == quantity
        assert result.status is OrderStatus.OPEN

    def test_soft_cancel_keeps_quantity(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()
        order = make_order(cycle_id=cycle.id, customer_id=customer.id)

        result = update_order(
            customer_id=customer.id,
            order_id=order.id,
            status=OrderStatus.CANCELLED,
            uow=SqlAlchemyUnitOfWork(),
            clock=Clock(),
        )

        assert result.id == order.id
        assert result.status is OrderStatus.CANCELLED
        assert result.quantity == order.quantity

    def test_already_cancelled(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()
        order = make_order(
            cycle_id=cycle.id,
            customer_id=customer.id,
            status=OrderStatus.CANCELLED,
        )

        with pytest.raises(OrderAlreadyCancelled):
            update_order(
                customer_id=customer.id,
                order_id=order.id,
                quantity=12,
                uow=SqlAlchemyUnitOfWork(),
                clock=Clock(),
            )

    def test_unknown_customer(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        order = make_order(cycle_id=cycle.id, customer_id=make_customer().id)

        with pytest.raises(CustomerNotFound):
            update_order(
                customer_id=0,
                order_id=order.id,
                quantity=12,
                uow=SqlAlchemyUnitOfWork(),
                clock=Clock(),
            )

    def test_unknown_order(self) -> None:
        customer = make_customer()

        with pytest.raises(OrderNotFound):
            update_order(
                customer_id=customer.id,
                order_id=0,
                quantity=12,
                uow=SqlAlchemyUnitOfWork(),
                clock=Clock(),
            )

    def test_other_customers_order(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        order = make_order(cycle_id=cycle.id, customer_id=make_customer().id)
        other = make_customer()

        with pytest.raises(OrderNotFound):
            update_order(
                customer_id=other.id,
                order_id=order.id,
                quantity=12,
                uow=SqlAlchemyUnitOfWork(),
                clock=Clock(),
            )

    def test_closed_cycle(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id, status=DeliveryCycleStatus.CLOSED)
        customer = make_customer()
        order = make_order(cycle_id=cycle.id, customer_id=customer.id)

        with pytest.raises(CycleAlreadyClosed):
            update_order(
                customer_id=customer.id,
                order_id=order.id,
                quantity=12,
                uow=SqlAlchemyUnitOfWork(),
                clock=Clock(),
            )

    def test_past_cutoff(self) -> None:
        clock = Clock()
        provider = make_provider()
        cycle = make_cycle(
            provider_id=provider.id,
            cutoff_at=clock.move_datetime_backward(days=2),
            delivery_at=clock.move_datetime_backward(days=1),
        )
        customer = make_customer()
        order = make_order(cycle_id=cycle.id, customer_id=customer.id)

        with pytest.raises(CycleAlreadyClosed):
            update_order(
                customer_id=customer.id,
                order_id=order.id,
                status=OrderStatus.CANCELLED,
                uow=SqlAlchemyUnitOfWork(),
                clock=clock,
            )

    def test_over_capacity(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id, max_eggs=12)
        make_order(cycle_id=cycle.id, customer_id=make_customer().id, quantity=8)
        customer = make_customer()
        order = make_order(cycle_id=cycle.id, customer_id=customer.id, quantity=2)

        with pytest.raises(CycleCapacityExceeded):
            update_order(
                customer_id=customer.id,
                order_id=order.id,
                quantity=6,
                uow=SqlAlchemyUnitOfWork(),
                clock=Clock(),
            )

    def test_decreases_quantity_at_capacity(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id, max_eggs=6)
        customer = make_customer()
        order = make_order(cycle_id=cycle.id, customer_id=customer.id, quantity=6)

        result = update_order(
            customer_id=customer.id,
            order_id=order.id,
            quantity=4,
            uow=SqlAlchemyUnitOfWork(),
            clock=Clock(),
        )

        assert result.quantity == 4
