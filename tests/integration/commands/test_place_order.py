import pytest

from src.commands.orders import place_order
from src.core.clock import Clock
from src.core.integrations.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from src.exceptions import (
    CustomerNotFound,
    CycleAlreadyClosed,
    CycleCapacityExceeded,
    CycleNotFound,
    OpenOrderAlreadyExists,
)
from src.models import DeliveryCycleStatus, OrderStatus
from src.schemas import OrderRead
from tests.generators import make_customer, make_cycle, make_order, make_provider
from tests.helpers import run_concurrently


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

    def test_open_order_already_exists(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()
        make_order(cycle_id=cycle.id, customer_id=customer.id)

        with pytest.raises(OpenOrderAlreadyExists):
            place_order(
                customer_id=customer.id,
                cycle_id=cycle.id,
                quantity=6,
                uow=SqlAlchemyUnitOfWork(),
                clock=Clock(),
            )

    def test_places_order_after_cancelled_one(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()
        make_order(
            cycle_id=cycle.id,
            customer_id=customer.id,
            status=OrderStatus.CANCELLED,
        )

        result = place_order(
            customer_id=customer.id,
            cycle_id=cycle.id,
            quantity=6,
            uow=SqlAlchemyUnitOfWork(),
            clock=Clock(),
        )

        assert result.status is OrderStatus.OPEN

    def test_places_order_with_open_order_in_other_cycle(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        other_cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()
        make_order(cycle_id=other_cycle.id, customer_id=customer.id)

        result = place_order(
            customer_id=customer.id,
            cycle_id=cycle.id,
            quantity=6,
            uow=SqlAlchemyUnitOfWork(),
            clock=Clock(),
        )

        assert result.cycle_id == cycle.id

    def test_concurrent_orders_respect_capacity(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id, max_eggs=10)
        customer_a = make_customer()
        customer_b = make_customer()

        def place(customer_id: int) -> OrderRead:
            return place_order(
                customer_id=customer_id,
                cycle_id=cycle.id,
                quantity=6,
                uow=SqlAlchemyUnitOfWork(),
                clock=Clock(),
            )

        outcomes = run_concurrently(
            lambda: place(customer_a.id), lambda: place(customer_b.id)
        )

        successes = [o for o in outcomes if isinstance(o, OrderRead)]
        failures = [o for o in outcomes if isinstance(o, CycleCapacityExceeded)]
        assert len(successes) == 1
        assert len(failures) == 1

    def test_concurrent_double_click_one_open_order(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()

        def place() -> OrderRead:
            return place_order(
                customer_id=customer.id,
                cycle_id=cycle.id,
                quantity=6,
                uow=SqlAlchemyUnitOfWork(),
                clock=Clock(),
            )

        outcomes = run_concurrently(place, place)

        successes = [o for o in outcomes if isinstance(o, OrderRead)]
        failures = [o for o in outcomes if isinstance(o, OpenOrderAlreadyExists)]
        assert len(successes) == 1
        assert len(failures) == 1
