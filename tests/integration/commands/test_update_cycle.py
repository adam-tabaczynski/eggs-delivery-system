import pytest

from src.commands.cycles import update_delivery_cycle
from src.commands.orders import place_order
from src.core.clock import Clock
from src.core.integrations.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from src.exceptions import (
    CycleAlreadyCancelled,
    CycleAlreadyClosed,
    CycleDeliveryPassed,
    CycleNotFound,
    ProviderNotFound,
)
from src.models import DeliveryCycleStatus, OrderStatus
from src.queries.orders import list_orders_for_cycle
from src.schemas import OrderRead
from tests.generators import make_customer, make_cycle, make_order, make_provider
from tests.helpers import run_concurrently


class TestUpdateDeliveryCycle:
    def test_closes_cycle(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()
        order = make_order(cycle_id=cycle.id, customer_id=customer.id)

        result = update_delivery_cycle(
            provider_id=provider.id,
            cycle_id=cycle.id,
            status=DeliveryCycleStatus.CLOSED,
            uow=SqlAlchemyUnitOfWork(),
            clock=Clock(),
        )

        assert result.id == cycle.id
        assert result.status is DeliveryCycleStatus.CLOSED
        assert result.provider_id == cycle.provider_id
        assert result.cutoff_at == cycle.cutoff_at
        assert result.delivery_at == cycle.delivery_at
        assert result.max_eggs == cycle.max_eggs
        assert result.allocated_eggs == order.quantity

    def test_unknown_provider(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)

        with pytest.raises(ProviderNotFound):
            update_delivery_cycle(
                provider_id=0,
                cycle_id=cycle.id,
                status=DeliveryCycleStatus.CLOSED,
                uow=SqlAlchemyUnitOfWork(),
                clock=Clock(),
            )

    def test_unknown_cycle(self) -> None:
        provider = make_provider()

        with pytest.raises(CycleNotFound):
            update_delivery_cycle(
                provider_id=provider.id,
                cycle_id=0,
                status=DeliveryCycleStatus.CLOSED,
                uow=SqlAlchemyUnitOfWork(),
                clock=Clock(),
            )

    def test_other_providers_cycle(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        other_provider = make_provider()

        with pytest.raises(CycleNotFound):
            update_delivery_cycle(
                provider_id=other_provider.id,
                cycle_id=cycle.id,
                status=DeliveryCycleStatus.CLOSED,
                uow=SqlAlchemyUnitOfWork(),
                clock=Clock(),
            )

    def test_already_closed(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id, status=DeliveryCycleStatus.CLOSED)

        with pytest.raises(CycleAlreadyClosed):
            update_delivery_cycle(
                provider_id=provider.id,
                cycle_id=cycle.id,
                status=DeliveryCycleStatus.CLOSED,
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

        with pytest.raises(CycleAlreadyClosed):
            update_delivery_cycle(
                provider_id=provider.id,
                cycle_id=cycle.id,
                status=DeliveryCycleStatus.CLOSED,
                uow=SqlAlchemyUnitOfWork(),
                clock=clock,
            )

    def test_concurrent_close_second_gets_conflict(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)

        def close() -> object:
            return update_delivery_cycle(
                provider_id=provider.id,
                cycle_id=cycle.id,
                status=DeliveryCycleStatus.CLOSED,
                uow=SqlAlchemyUnitOfWork(),
                clock=Clock(),
            )

        outcomes = run_concurrently(close, close)

        assert sum(isinstance(o, CycleAlreadyClosed) for o in outcomes) == 1
        assert sum(not isinstance(o, Exception) for o in outcomes) == 1

    def test_cancels_cycle(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()
        make_order(cycle_id=cycle.id, customer_id=customer.id)

        result = update_delivery_cycle(
            provider_id=provider.id,
            cycle_id=cycle.id,
            status=DeliveryCycleStatus.CANCELLED,
            uow=SqlAlchemyUnitOfWork(),
            clock=Clock(),
        )

        assert result.id == cycle.id
        assert result.status is DeliveryCycleStatus.CANCELLED
        assert result.allocated_eggs == 0

    def test_cancels_closed_cycle_after_cutoff(self) -> None:
        clock = Clock()
        provider = make_provider()
        cycle = make_cycle(
            provider_id=provider.id,
            cutoff_at=clock.move_datetime_backward(days=1),
            delivery_at=clock.move_datetime_forward(days=1),
            status=DeliveryCycleStatus.CLOSED,
        )

        result = update_delivery_cycle(
            provider_id=provider.id,
            cycle_id=cycle.id,
            status=DeliveryCycleStatus.CANCELLED,
            uow=SqlAlchemyUnitOfWork(),
            clock=clock,
        )

        assert result.status is DeliveryCycleStatus.CANCELLED

    def test_cancel_unknown_cycle(self) -> None:
        provider = make_provider()

        with pytest.raises(CycleNotFound):
            update_delivery_cycle(
                provider_id=provider.id,
                cycle_id=0,
                status=DeliveryCycleStatus.CANCELLED,
                uow=SqlAlchemyUnitOfWork(),
                clock=Clock(),
            )

    def test_cancel_other_providers_cycle(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        other_provider = make_provider()

        with pytest.raises(CycleNotFound):
            update_delivery_cycle(
                provider_id=other_provider.id,
                cycle_id=cycle.id,
                status=DeliveryCycleStatus.CANCELLED,
                uow=SqlAlchemyUnitOfWork(),
                clock=Clock(),
            )

    def test_cancel_already_cancelled(self) -> None:
        provider = make_provider()
        cycle = make_cycle(
            provider_id=provider.id, status=DeliveryCycleStatus.CANCELLED
        )

        with pytest.raises(CycleAlreadyCancelled):
            update_delivery_cycle(
                provider_id=provider.id,
                cycle_id=cycle.id,
                status=DeliveryCycleStatus.CANCELLED,
                uow=SqlAlchemyUnitOfWork(),
                clock=Clock(),
            )

    def test_cancel_after_delivery(self) -> None:
        clock = Clock()
        provider = make_provider()
        cycle = make_cycle(
            provider_id=provider.id,
            cutoff_at=clock.move_datetime_backward(days=2),
            delivery_at=clock.move_datetime_backward(days=1),
        )

        with pytest.raises(CycleDeliveryPassed):
            update_delivery_cycle(
                provider_id=provider.id,
                cycle_id=cycle.id,
                status=DeliveryCycleStatus.CANCELLED,
                uow=SqlAlchemyUnitOfWork(),
                clock=clock,
            )

    def test_close_cancelled_cycle(self) -> None:
        provider = make_provider()
        cycle = make_cycle(
            provider_id=provider.id, status=DeliveryCycleStatus.CANCELLED
        )

        with pytest.raises(CycleAlreadyCancelled):
            update_delivery_cycle(
                provider_id=provider.id,
                cycle_id=cycle.id,
                status=DeliveryCycleStatus.CLOSED,
                uow=SqlAlchemyUnitOfWork(),
                clock=Clock(),
            )

    def test_concurrent_cancel_and_place_order_leave_no_open_order(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()

        def cancel() -> object:
            return update_delivery_cycle(
                provider_id=provider.id,
                cycle_id=cycle.id,
                status=DeliveryCycleStatus.CANCELLED,
                uow=SqlAlchemyUnitOfWork(),
                clock=Clock(),
            )

        def place() -> object:
            return place_order(
                customer_id=customer.id,
                cycle_id=cycle.id,
                quantity=6,
                uow=SqlAlchemyUnitOfWork(),
                clock=Clock(),
            )

        cancel_outcome, place_outcome = run_concurrently(cancel, place)

        assert not isinstance(cancel_outcome, Exception)
        assert isinstance(place_outcome, OrderRead | CycleAlreadyCancelled)
        # Read back: the race is only visible in what's left in the cycle.
        open_orders = list_orders_for_cycle(
            provider_id=provider.id,
            cycle_id=cycle.id,
            status=OrderStatus.OPEN,
            uow=SqlAlchemyUnitOfWork(),
        )
        assert open_orders == []
