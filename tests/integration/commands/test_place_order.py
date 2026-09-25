import pytest

from src.commands.orders import place_order
from src.core.clock import Clock
from src.core.integrations.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from src.exceptions import (
    CustomerNotFound,
    CycleAlreadyClosed,
    CycleCapacityExceeded,
    CycleNotFound,
)
from src.models import DeliveryCycleStatus, OrderStatus
from tests.generators import make_customer, make_cycle, make_order, make_provider


class TestPlaceOrder:
    def test_places_order(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()
        quantity = 6

        result = place_order(
            customer_id=customer.id,
            cycle_id=cycle.id,
            quantity=quantity,
            uow=SqlAlchemyUnitOfWork(),
            clock=Clock(),
        )

        assert result.customer_id == customer.id
        assert result.cycle_id == cycle.id
        assert result.quantity == quantity
        assert result.status is OrderStatus.OPEN

    def test_unknown_customer(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)

        with pytest.raises(CustomerNotFound):
            place_order(
                customer_id=0,
                cycle_id=cycle.id,
                quantity=6,
                uow=SqlAlchemyUnitOfWork(),
                clock=Clock(),
            )

    def test_unknown_cycle(self) -> None:
        customer = make_customer()

        with pytest.raises(CycleNotFound):
            place_order(
                customer_id=customer.id,
                cycle_id=0,
                quantity=6,
                uow=SqlAlchemyUnitOfWork(),
                clock=Clock(),
            )

    def test_closed_cycle(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id, status=DeliveryCycleStatus.CLOSED)
        customer = make_customer()

        with pytest.raises(CycleAlreadyClosed):
            place_order(
                customer_id=customer.id,
                cycle_id=cycle.id,
                quantity=6,
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

        with pytest.raises(CycleAlreadyClosed):
            place_order(
                customer_id=customer.id,
                cycle_id=cycle.id,
                quantity=6,
                uow=SqlAlchemyUnitOfWork(),
                clock=clock,
            )

    def test_fills_remaining_capacity(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id, max_eggs=12)
        other_customer = make_customer()
        make_order(cycle_id=cycle.id, customer_id=other_customer.id, quantity=6)
        customer = make_customer()

        result = place_order(
            customer_id=customer.id,
            cycle_id=cycle.id,
            quantity=6,
            uow=SqlAlchemyUnitOfWork(),
            clock=Clock(),
        )

        assert result.quantity == 6

    def test_over_capacity(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id, max_eggs=12)
        other_customer = make_customer()
        make_order(cycle_id=cycle.id, customer_id=other_customer.id, quantity=8)
        customer = make_customer()

        with pytest.raises(CycleCapacityExceeded):
            place_order(
                customer_id=customer.id,
                cycle_id=cycle.id,
                quantity=6,
                uow=SqlAlchemyUnitOfWork(),
                clock=Clock(),
            )

    def test_ignores_cancelled_quantity(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id, max_eggs=6)
        other_customer = make_customer()
        make_order(
            cycle_id=cycle.id,
            customer_id=other_customer.id,
            quantity=6,
            status=OrderStatus.CANCELLED,
        )
        customer = make_customer()

        result = place_order(
            customer_id=customer.id,
            cycle_id=cycle.id,
            quantity=6,
            uow=SqlAlchemyUnitOfWork(),
            clock=Clock(),
        )

        assert result.quantity == 6
