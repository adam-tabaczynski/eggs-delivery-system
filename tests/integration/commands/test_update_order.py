import threading

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
from src.schemas import OrderRead
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
        customer = make_customer()
        order = make_order(cycle_id=cycle.id, customer_id=customer.id)

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
        customer = make_customer()
        order = make_order(cycle_id=cycle.id, customer_id=customer.id)
        other_customer = make_customer()

        with pytest.raises(OrderNotFound):
            update_order(
                customer_id=other_customer.id,
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
        other_customer = make_customer()
        make_order(cycle_id=cycle.id, customer_id=other_customer.id, quantity=8)
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

    def test_concurrent_double_cancel(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()
        order = make_order(cycle_id=cycle.id, customer_id=customer.id)
        barrier = threading.Barrier(2)
        results: list[OrderRead | Exception] = []
        results_lock = threading.Lock()

        def cancel() -> None:
            barrier.wait()
            try:
                result: OrderRead | Exception = update_order(
                    customer_id=customer.id,
                    order_id=order.id,
                    status=OrderStatus.CANCELLED,
                    uow=SqlAlchemyUnitOfWork(),
                    clock=Clock(),
                )
            except OrderAlreadyCancelled as exc:
                result = exc
            with results_lock:
                results.append(result)

        threads = [threading.Thread(target=cancel) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        successes = [r for r in results if isinstance(r, OrderRead)]
        failures = [r for r in results if isinstance(r, OrderAlreadyCancelled)]
        assert len(successes) == 1
        assert len(failures) == 1

    def test_concurrent_quantity_increases_respect_capacity(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id, max_eggs=10)
        customer_a = make_customer()
        customer_b = make_customer()
        order_a = make_order(cycle_id=cycle.id, customer_id=customer_a.id, quantity=2)
        order_b = make_order(cycle_id=cycle.id, customer_id=customer_b.id, quantity=2)
        barrier = threading.Barrier(2)
        results: dict[str, OrderRead | Exception] = {}

        def increase(name: str, customer_id: int, order_id: int) -> None:
            barrier.wait()
            try:
                results[name] = update_order(
                    customer_id=customer_id,
                    order_id=order_id,
                    quantity=8,
                    uow=SqlAlchemyUnitOfWork(),
                    clock=Clock(),
                )
            except CycleCapacityExceeded as exc:
                results[name] = exc

        thread_a = threading.Thread(
            target=increase, args=("a", customer_a.id, order_a.id)
        )
        thread_b = threading.Thread(
            target=increase, args=("b", customer_b.id, order_b.id)
        )
        thread_a.start()
        thread_b.start()
        thread_a.join()
        thread_b.join()

        outcomes = list(results.values())
        successes = [o for o in outcomes if isinstance(o, OrderRead)]
        failures = [o for o in outcomes if isinstance(o, CycleCapacityExceeded)]
        assert len(successes) == 1
        assert len(failures) == 1
