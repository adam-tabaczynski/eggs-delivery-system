import pytest

from src.core.clock import Clock
from src.core.integrations.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from src.exceptions import CustomerNotFound
from src.models import DeliveryCycleStatus, OrderStatus
from src.queries.cycles import list_cycles_for_customer
from tests.generators import make_customer, make_cycle, make_order, make_provider


class TestListCyclesForCustomer:
    def test_lists_open_and_past_cycles(self) -> None:
        clock = Clock()
        provider = make_provider()
        opened = make_cycle(provider_id=provider.id)
        past = make_cycle(
            provider_id=provider.id,
            cutoff_at=clock.move_datetime_backward(days=2),
            delivery_at=clock.move_datetime_backward(days=1),
        )
        customer = make_customer()

        result = list_cycles_for_customer(
            customer_id=customer.id, uow=SqlAlchemyUnitOfWork(), clock=clock
        )

        statuses = {
            cycle.id: cycle.status
            for cycle in result
            if cycle.id in {opened.id, past.id}
        }
        assert statuses == {
            past.id: DeliveryCycleStatus.CLOSED,
            opened.id: DeliveryCycleStatus.OPEN,
        }

    def test_reports_allocated_eggs(self) -> None:
        provider = make_provider()
        customer = make_customer()
        other_customer = make_customer()
        open_cycle = make_cycle(provider_id=provider.id)
        make_order(
            cycle_id=open_cycle.id,
            customer_id=customer.id,
            quantity=6,
            status=OrderStatus.OPEN,
        )
        make_order(
            cycle_id=open_cycle.id,
            customer_id=other_customer.id,
            quantity=12,
            status=OrderStatus.OPEN,
        )
        make_order(
            cycle_id=open_cycle.id,
            customer_id=customer.id,
            quantity=30,
            status=OrderStatus.CANCELLED,
        )
        closed_cycle = make_cycle(
            provider_id=provider.id, status=DeliveryCycleStatus.CLOSED
        )
        make_order(
            cycle_id=closed_cycle.id,
            customer_id=other_customer.id,
            quantity=10,
            status=OrderStatus.OPEN,
        )
        empty_cycle = make_cycle(provider_id=provider.id)

        result = list_cycles_for_customer(
            customer_id=customer.id, uow=SqlAlchemyUnitOfWork(), clock=Clock()
        )

        created = {open_cycle.id, closed_cycle.id, empty_cycle.id}
        by_id = {
            listed.id: listed.allocated_eggs
            for listed in result
            if listed.id in created
        }
        assert by_id == {open_cycle.id: 18, closed_cycle.id: 10, empty_cycle.id: 0}

    def test_unknown_customer(self) -> None:
        with pytest.raises(CustomerNotFound):
            list_cycles_for_customer(
                customer_id=0, uow=SqlAlchemyUnitOfWork(), clock=Clock()
            )
