import pytest

from src.core.integrations.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from src.exceptions import CycleNotFound, ProviderNotFound
from src.models import DeliveryCycleStatus, OrderStatus
from src.queries.orders import list_orders_for_cycle
from tests.generators import make_customer, make_cycle, make_order, make_provider


class TestListOrdersForCycle:
    def test_lists_open_and_cancelled_orders(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()
        other_customer = make_customer()
        opened = make_order(cycle_id=cycle.id, customer_id=customer.id, quantity=12)
        cancelled = make_order(
            cycle_id=cycle.id,
            customer_id=other_customer.id,
            quantity=6,
            status=OrderStatus.CANCELLED,
        )

        result = list_orders_for_cycle(
            provider_id=provider.id, cycle_id=cycle.id, uow=SqlAlchemyUnitOfWork()
        )

        by_id = {order.id: order for order in result}
        assert by_id.keys() == {opened.id, cancelled.id}
        assert by_id[opened.id].customer_id == customer.id
        assert by_id[opened.id].status is OrderStatus.OPEN
        assert by_id[opened.id].quantity == opened.quantity
        assert by_id[cancelled.id].customer_id == other_customer.id
        assert by_id[cancelled.id].status is OrderStatus.CANCELLED
        assert by_id[cancelled.id].quantity == cancelled.quantity

    def test_lists_in_placement_order(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        first_customer = make_customer()
        second_customer = make_customer()
        third_customer = make_customer()
        first = make_order(cycle_id=cycle.id, customer_id=first_customer.id)
        second = make_order(cycle_id=cycle.id, customer_id=second_customer.id)
        third = make_order(cycle_id=cycle.id, customer_id=third_customer.id)

        result = list_orders_for_cycle(
            provider_id=provider.id, cycle_id=cycle.id, uow=SqlAlchemyUnitOfWork()
        )

        assert [order.id for order in result] == [first.id, second.id, third.id]

    def test_isolates_cycles(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        other_cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()
        own = make_order(cycle_id=cycle.id, customer_id=customer.id)
        make_order(cycle_id=other_cycle.id, customer_id=customer.id)

        result = list_orders_for_cycle(
            provider_id=provider.id, cycle_id=cycle.id, uow=SqlAlchemyUnitOfWork()
        )

        assert [order.id for order in result] == [own.id]

    def test_lists_orders_of_closed_cycle(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id, status=DeliveryCycleStatus.CLOSED)
        customer = make_customer()
        order = make_order(cycle_id=cycle.id, customer_id=customer.id)

        result = list_orders_for_cycle(
            provider_id=provider.id, cycle_id=cycle.id, uow=SqlAlchemyUnitOfWork()
        )

        assert [(listed.id, listed.status) for listed in result] == [
            (order.id, OrderStatus.OPEN)
        ]

    def test_unknown_provider(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)

        with pytest.raises(ProviderNotFound):
            list_orders_for_cycle(
                provider_id=0, cycle_id=cycle.id, uow=SqlAlchemyUnitOfWork()
            )

    def test_unknown_cycle(self) -> None:
        provider = make_provider()

        with pytest.raises(CycleNotFound):
            list_orders_for_cycle(
                provider_id=provider.id, cycle_id=0, uow=SqlAlchemyUnitOfWork()
            )

    def test_other_providers_cycle(self) -> None:
        provider = make_provider()
        other_provider = make_provider()
        other_cycle = make_cycle(provider_id=other_provider.id)

        with pytest.raises(CycleNotFound):
            list_orders_for_cycle(
                provider_id=provider.id,
                cycle_id=other_cycle.id,
                uow=SqlAlchemyUnitOfWork(),
            )
