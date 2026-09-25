import pytest

from src.core.integrations.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from src.exceptions import CustomerNotFound
from src.models import DeliveryCycleStatus, OrderStatus
from src.queries.orders import list_orders_for_customer
from tests.generators import make_customer, make_cycle, make_order, make_provider


class TestListOrdersForCustomer:
    def test_lists_open_and_cancelled_orders(self) -> None:
        provider = make_provider()
        customer = make_customer()
        opened = make_order(
            cycle_id=make_cycle(provider_id=provider.id).id,
            customer_id=customer.id,
            quantity=12,
        )
        cancelled = make_order(
            cycle_id=make_cycle(provider_id=provider.id).id,
            customer_id=customer.id,
            quantity=6,
            status=OrderStatus.CANCELLED,
        )

        result = list_orders_for_customer(
            customer_id=customer.id, uow=SqlAlchemyUnitOfWork()
        )

        by_id = {order.id: order for order in result}
        assert by_id.keys() == {opened.id, cancelled.id}
        assert by_id[opened.id].status is OrderStatus.OPEN
        assert by_id[opened.id].quantity == opened.quantity
        assert by_id[cancelled.id].status is OrderStatus.CANCELLED
        assert by_id[cancelled.id].quantity == cancelled.quantity

    def test_isolates_customers(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()
        own = make_order(cycle_id=cycle.id, customer_id=customer.id)
        make_order(cycle_id=cycle.id, customer_id=make_customer().id)

        result = list_orders_for_customer(
            customer_id=customer.id, uow=SqlAlchemyUnitOfWork()
        )

        assert [order.id for order in result] == [own.id]

    def test_lists_orders_of_closed_cycle(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id, status=DeliveryCycleStatus.CLOSED)
        customer = make_customer()
        order = make_order(cycle_id=cycle.id, customer_id=customer.id)

        result = list_orders_for_customer(
            customer_id=customer.id, uow=SqlAlchemyUnitOfWork()
        )

        assert [(listed.id, listed.status) for listed in result] == [
            (order.id, OrderStatus.OPEN)
        ]

    def test_unknown_customer(self) -> None:
        with pytest.raises(CustomerNotFound):
            list_orders_for_customer(customer_id=0, uow=SqlAlchemyUnitOfWork())
